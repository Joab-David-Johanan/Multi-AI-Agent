from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_tavily import TavilySearch
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from fastapi.responses import StreamingResponse
import asyncio


# getting the assistant prompt dictionary
from multi_agent_app.config.settings import settings


# Return the correct LLM instance based on provider selected in the UI
def get_llm(provider: str, model_name: str, streaming: bool):

    if provider == "Groq":
        return ChatGroq(model=model_name, streaming=streaming)

    elif provider == "OpenAI":
        return ChatOpenAI(model=model_name, streaming=streaming)

    else:
        raise ValueError("Unsupported LLM provider")


# Main function responsible for generating AI responses
# This function is asynchronous because model invocation is async
async def generate_response(
    assistant_type: str,
    llm_type: str,
    llm_model: str,
    query: str,
    allow_search: bool,
    enable_streaming: bool,
):
    assistant_type = assistant_type
    # Select assistant-specific instructions
    assistant_prompt = settings.ASSISTANT_PROMPTS[assistant_type]

    # Initialize the selected LLM
    llm = get_llm(provider=llm_type, model_name=llm_model, streaming=enable_streaming)

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
    tools = [TavilySearch(max_results=5)] if use_search else []

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
    """

    # Combine guardrails with assistant-specific instructions
    final_system_prompt = (
        BASE_SYSTEM_PROMPT + "\n\nAdditional instructions:\n" + assistant_prompt
    )

    # Create LangGraph agent
    agent = create_react_agent(model=llm, tools=tools)

    state = {
        "messages": [
            SystemMessage(content=final_system_prompt),
            HumanMessage(content=query),
        ]
    }

    if streaming:

        # Run agent normally first
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
        response = await agent.ainvoke(state)

        # Check messages list
        if "messages" in response:
            for message in reversed(response["messages"]):
                if isinstance(message, AIMessage):
                    return message.content

        # If response structure is unexpected
        raise ValueError("Unexpected agent response structure")
