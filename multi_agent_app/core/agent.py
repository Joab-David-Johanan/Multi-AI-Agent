from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_tavily import TavilySearch
from langchain_core.messages import AIMessage

# getting the assistant prompt dictionary
from multi_agent_app.config.settings import settings


# Return the correct LLM instance based on provider selected in the UI
def get_llm(provider: str, model_name: str):

    if provider == "Groq":
        return ChatGroq(model=model_name)

    elif provider == "OpenAI":
        return ChatOpenAI(model=model_name)

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
):
    assistant_type = assistant_type
    # Select assistant-specific instructions
    assistant_prompt = settings.ASSISTANT_PROMPTS[assistant_type]

    # Initialize the selected LLM
    llm = get_llm(llm_type, llm_model)

    # ------------------------------------------------------------------
    # NEW LOGIC: Disable search for basic knowledge questions
    # ------------------------------------------------------------------
    # Simple educational questions do not require web search.
    # This prevents irrelevant tool usage.
    basic_question_starters = ["what is", "define", "explain"]

    price_keywords = ["price", "now", "current", "today"]

    use_search = allow_search

    # Some models misbehave with trailing spaces.
    query = query.strip()

    if any(query.lower().startswith(k) for k in basic_question_starters):
        if not any(p in query.lower() for p in price_keywords):
            use_search = False

    # Add Tavily search tool only if needed
    tools = [TavilySearch(max_results=2)] if use_search else []

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

    # Create LangChain agent
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=final_system_prompt,
    )

    # Invoke agent asynchronously
    response = await agent.ainvoke({"input": query})

    # Some LangChain versions return dictionary with "output"
    if "output" in response:
        return response["output"]

    # Other versions return a messages list
    if "messages" in response:
        for message in reversed(response["messages"]):
            if isinstance(message, AIMessage):
                return message.content

    # If response structure is unexpected
    raise ValueError("Unexpected agent response structure")
