from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_tavily import TavilySearch
from langchain_core.messages import AIMessage


# Return the correct LLM instance based on provider selected in the UI
def get_llm(provider: str, model_name: str):

    if provider == "Groq":
        return ChatGroq(model=model_name)

    elif provider == "OpenAI":
        return ChatOpenAI(model=model_name)

    else:
        raise ValueError("Unsupported LLM provider")


# Return the correct system prompt based on selected assistant
def get_correct_prompt(assistant: str, assistant_prompt: dict[str, str]):

    if assistant == "General":
        return assistant_prompt["General"]

    elif assistant == "Medical":
        return assistant_prompt["Medical"]

    elif assistant == "Financial":
        return assistant_prompt["Financial"]

    elif assistant == "Research":
        return assistant_prompt["Research"]

    else:
        raise ValueError("Unsupported AI assistant")


# Main function responsible for generating AI responses
# This function is asynchronous because model invocation is async
async def generate_response(
    assistant_type: str,
    all_assistant_prompts: dict[str, str],
    llm_type: str,
    llm_model: str,
    query: str,
    allow_search: bool,
):

    # Select assistant-specific instructions
    assistant_prompt = get_correct_prompt(assistant_type, all_assistant_prompts)

    # Initialize the selected LLM
    llm = get_llm(llm_type, llm_model)

    # ------------------------------------------------------------------
    # NEW LOGIC: Disable search for basic knowledge questions
    # ------------------------------------------------------------------
    # Simple educational questions do not require web search.
    # This prevents irrelevant tool usage.
    basic_question_starters = ["what is", "define", "explain"]

    use_search = allow_search

    if any(query.lower().startswith(k) for k in basic_question_starters):
        use_search = False

    # Add Tavily search tool only if needed
    tools = [TavilySearch(max_results=2)] if use_search else []

    # ------------------------------------------------------------------
    # Improved base guardrails
    # ------------------------------------------------------------------
    BASE_SYSTEM_PROMPT = """
You are a professional AI assistant.

Rules:
- Always answer the user's question directly and immediately.
- Do not greet the user.
- Do not ask the user what they want to know.
- Do not ask them to clarify unless absolutely necessary.
- Do not restate the question.
- Only use web search if the question requires current or real-time information.
- Do not use web search for general knowledge explanations.
- If web search results are unrelated, ignore them.
- Prefer accurate domain knowledge over irrelevant summaries.
- If uncertain, clearly state limitations.
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
