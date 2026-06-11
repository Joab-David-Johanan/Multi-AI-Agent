import json
import re

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from fastapi.responses import StreamingResponse


from multi_agent_app.config.settings import settings
from multi_agent_app.core.helper import get_llm, get_agent
from multi_agent_app.core.helper import TAVILY_TOOL

STREAM_METADATA_MARKER = "\n[[STREAM_METADATA]]"


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


def parse_agent_content(content: str):
    answer = content
    suggestions = []

    suggestion_match = re.search(r"\bSUGGESTIONS\s*:?", content)
    if suggestion_match:
        parts = [
            content[: suggestion_match.start()],
            content[suggestion_match.end() :],
        ]
        answer = parts[0].replace("ANSWER:", "").strip()

        suggestion_lines = parts[1].strip().split("\n")
        for line in suggestion_lines:
            line = line.strip()
            if line and line[0].isdigit():
                suggestions.append(line[2:].strip())

    return answer, suggestions


def text_streaming_response(text: str):
    async def stream_once():
        yield text

    return StreamingResponse(stream_once(), media_type="text/plain")


async def invoke_agent(agent, state, config):
    if config:
        return await agent.ainvoke(state, config=config)

    return await agent.ainvoke(state)


def extract_stream_content(event) -> str:
    message = event[0] if isinstance(event, tuple) else event
    content = getattr(message, "content", "")

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(item.get("text") or item.get("content") or "")
        return "".join(parts)

    return ""


def get_visible_stream_answer(raw_text: str):
    text = raw_text.lstrip()
    answer_prefix = "ANSWER:"
    suggestion_marker = "SUGGESTIONS"

    if answer_prefix.startswith(text) and text != answer_prefix:
        return None, False

    if text.startswith(answer_prefix):
        text = text[len(answer_prefix) :].lstrip()

    suggestion_match = re.search(r"\bSUGGESTIONS\s*:?", text)
    if suggestion_match:
        text = text[: suggestion_match.start()].rstrip()
        return text, True

    stripped_text = text.rstrip()
    upper_text = stripped_text.upper()
    for marker_length in range(len(suggestion_marker) - 1, 0, -1):
        partial_marker = suggestion_marker[:marker_length]
        if upper_text.endswith(partial_marker):
            visible_text = stripped_text[: -marker_length].rstrip()
            return visible_text, False

    return text, False


def agent_streaming_response(agent, state, config):
    async def stream_answer():
        raw_text = ""
        emitted_length = 0

        stream_kwargs = {"stream_mode": "messages"}
        if config:
            stream_kwargs["config"] = config

        stream = agent.astream(state, **stream_kwargs)

        async for event in stream:
            chunk = extract_stream_content(event)
            if not chunk:
                continue

            raw_text += chunk
            visible_text, should_stop = get_visible_stream_answer(raw_text)
            if visible_text is None:
                continue

            next_chunk = visible_text[emitted_length:]
            if next_chunk:
                emitted_length = len(visible_text)
                yield next_chunk

            if should_stop:
                continue

        _, suggestions = parse_agent_content(raw_text)
        if suggestions:
            yield STREAM_METADATA_MARKER + json.dumps({"suggestions": suggestions})

    return StreamingResponse(stream_answer(), media_type="text/plain")


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
            return text_streaming_response(small_talk_response["answer"])

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
        return agent_streaming_response(agent, state, config)

    else:

        # Invoke agent asynchronously and no streaming response
        response = await invoke_agent(agent, state, config)

        # Check messages list
        if "messages" in response:
            for message in reversed(response["messages"]):
                if isinstance(message, AIMessage):

                    content = message.content

                    answer, suggestions = parse_agent_content(content)

                    return {"answer": answer, "suggestions": suggestions}

        # If response structure is unexpected
        raise ValueError("Unexpected agent response structure")
