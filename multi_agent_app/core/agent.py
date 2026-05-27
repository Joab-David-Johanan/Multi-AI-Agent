from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_tavily import TavilySearch
from fastapi.responses import StreamingResponse
import asyncio


from multi_agent_app.config.settings import settings
from multi_agent_app.core.helper import get_llm, get_agent, get_cached_search
from multi_agent_app.core.helper import TAVILY_TOOL


GREETING_INPUTS = {
    "hi",
    "hello",
    "hey",
    "hiya",
    "good morning",
    "good afternoon",
    "good evening",
}

THANKS_INPUTS = {
    "thanks",
    "thank you",
    "thx",
    "ty",
}

ASSISTANT_GREETING_RESPONSES = {
    "General": {
        "answer": "Hello. Ask me anything you want help with, and I will keep the answer clear and useful.",
        "suggestions": [
            "Explain a concept clearly",
            "Compare two options",
            "Draft or improve text",
        ],
    },
    "Medical": {
        "answer": "Hello. I can help with general health and medical information, but I cannot diagnose conditions.",
        "suggestions": [
            "Ask about a health condition",
            "Review general symptom information",
            "Discuss treatment options to ask a clinician about",
        ],
    },
    "Financial": {
        "answer": "Hello. I can help with educational finance, investing, market, and economics questions.",
        "suggestions": [
            "Explain an investing concept",
            "Compare financial risks",
            "Review a market or economics topic",
        ],
    },
    "Law": {
        "answer": "Hello. I can help with general legal information, but I cannot provide personalized legal advice.",
        "suggestions": [
            "Explain a legal concept",
            "Compare legal procedures",
            "Discuss jurisdiction-specific considerations",
        ],
    },
}


def get_small_talk_response(assistant_type: str, query: str):
    normalized_query = " ".join(query.lower().strip().split())

    if normalized_query in GREETING_INPUTS:
        return ASSISTANT_GREETING_RESPONSES[assistant_type]

    if normalized_query in THANKS_INPUTS:
        return {
            "answer": "You're welcome.",
            "suggestions": ASSISTANT_GREETING_RESPONSES[assistant_type]["suggestions"],
        }

    return None


def as_streaming_response(text: str):
    async def fake_stream():
        for char in text:
            yield char
            await asyncio.sleep(0.01)

    return StreamingResponse(fake_stream(), media_type="text/plain")


# Main function responsible for generating AI responses
# This function is asynchronous because model invocation is async
async def generate_response(
    assistant_type: str,
    llm_type: str,
    llm_model: str,
    temperature: int,
    query: str,
    allow_search: bool,
    enable_streaming: bool,
    thread_id: str,  # for conversational memory
    enable_memory: bool,
):
    # Some models over-restrict assistant prompts and reject greetings. Handle
    # obvious small talk locally so domain guardrails still stay intact.
    query = query.strip()
    small_talk_response = get_small_talk_response(assistant_type, query)

    if small_talk_response:
        if enable_streaming:
            return as_streaming_response(small_talk_response["answer"])

        return small_talk_response

    # Select assistant-specific instructions
    assistant_prompt = settings.ASSISTANT_PROMPTS[assistant_type]

    # Initialize the selected LLM
    llm = get_llm(
        provider=llm_type,
        model_name=llm_model,
        streaming=enable_streaming,
        temperature=temperature,
    )

    # ------------------------------------------------------------------
    # NEW LOGIC: Disable search for basic knowledge questions
    # ------------------------------------------------------------------
    # Simple educational questions do not require web search.
    # This prevents irrelevant tool usage.
    basic_question_starters = ["what is", "define", "explain"]

    price_keywords = ["price", "now", "current", "today"]

    # tool search
    use_search = allow_search

    if any(query.lower().startswith(k) for k in basic_question_starters):
        if not any(p in query.lower() for p in price_keywords):
            use_search = False

    # streaming
    streaming = enable_streaming

    # Add Tavily search tool only if needed
    tools = [TAVILY_TOOL] if use_search else []

    # ------------------------------------------------------------------
    # Improved base guardrails
    # ------------------------------------------------------------------

    BASE_SYSTEM_PROMPT = """
    You are a professional AI assistant.

    Strict rules:
    - You MUST answer the user's question immediately.
    - You MUST NOT introduce yourself.
    - You MUST NOT say you are ready to help unless the user only sent a greeting or thanks.
    - You MUST NOT ask what the question is.
    - Never generate meta conversation.
    - Provide the final answer directly.
    - If the question is about current prices, provide the latest known estimate and mention it may not be real-time.
    - If the user only sends a greeting, thanks, or a short conversational setup message, respond briefly and politely.
    - Do not treat greetings, thanks, or "what can you do?" as out-of-domain requests.

    After the answer, you MUST provide exactly 3 short follow-up suggestions
    that help continue the conversation. The suggestions SHOULD NOT be questions but CLEAR FOLLOW-UPS.
    This output format is mandatory for every response, including greetings, refusals, and safety disclaimers.

    Output format MUST be:

    ANSWER:
    <final answer>

    SUGGESTIONS:
    1. ...
    2. ...
    3. ...
    """

    # Combine guardrails with assistant-specific instructions
    final_system_prompt = (
        BASE_SYSTEM_PROMPT + "\n\nAdditional instructions:\n" + assistant_prompt
    )

    state = {
        "messages": [
            SystemMessage(content=final_system_prompt),
            HumanMessage(content=query),
        ]
    }

    # Get the right agent based on UI selection
    agent = get_agent(llm, tools, enable_memory)

    # Prepare config only if memory is enabled
    config = {"configurable": {"thread_id": thread_id}} if enable_memory else None

    if streaming:

        # Run agent normally first
        if enable_memory:
            response = await agent.ainvoke(state, config=config)
        else:
            response = await agent.ainvoke(state)

        final_text = ""

        if "messages" in response:
            for message in reversed(response["messages"]):
                if isinstance(message, AIMessage):
                    final_text = message.content
                    break

        return as_streaming_response(final_text)

    else:

        # Invoke agent asynchronously and no streaming response
        if enable_memory:
            response = await agent.ainvoke(state, config=config)
        else:
            response = await agent.ainvoke(state)

        # Check messages list
        if "messages" in response:
            for message in reversed(response["messages"]):
                if isinstance(message, AIMessage):

                    content = message.content

                    answer = content
                    suggestions = []

                    if "SUGGESTIONS:" in content:
                        parts = content.split("SUGGESTIONS:")
                        answer = parts[0].replace("ANSWER:", "").strip()

                        suggestion_lines = parts[1].strip().split("\n")

                        for line in suggestion_lines:
                            line = line.strip()
                            if line and line[0].isdigit():
                                suggestions.append(line[2:].strip())

                    return {"answer": answer, "suggestions": suggestions}

        # If response structure is unexpected
        raise ValueError("Unexpected agent response structure")
