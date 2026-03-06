from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_tavily import TavilySearch
from fastapi.responses import StreamingResponse
import asyncio


from multi_agent_app.config.settings import settings
from multi_agent_app.core.helper import get_llm, get_agent, get_cached_search
from multi_agent_app.core.helper import TAVILY_TOOL


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

    # Some models misbehave with trailing spaces.
    query = query.strip()

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
    - You MUST NOT say you are ready to help.
    - You MUST NOT ask what the question is.
    - Never generate meta conversation.
    - Provide the final answer directly.
    - If the question is about current prices, provide the latest known estimate and mention it may not be real-time.

    After the answer, you MUST provide exactly 3 short follow-up suggestions
    that help continue the conversation.

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

        async def fake_stream():
            for char in final_text:
                yield char
                await asyncio.sleep(0.01)  # adjust speed here

        return StreamingResponse(fake_stream(), media_type="text/plain")

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
