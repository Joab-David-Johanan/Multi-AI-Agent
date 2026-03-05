from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

# LangGraph memory checkpoint (persistent during runtime)
memory = MemorySaver()

# -------------------------------------------------
# GLOBAL CACHES (avoid recreating agents + llms)
# -------------------------------------------------

LLM_CACHE = {}
AGENT_CACHE = {}


# This ensures LLM instance is reused
def get_llm(provider: str, model_name: str, streaming: bool, temperature: int):

    cache_key = (provider, model_name, streaming, temperature)

    if cache_key in LLM_CACHE:
        return LLM_CACHE[cache_key]

    if provider == "Groq":
        llm = ChatGroq(
            model=model_name,
            streaming=streaming,
            temperature=temperature,
        )

    elif provider == "OpenAI":
        llm = ChatOpenAI(
            model=model_name,
            streaming=streaming,
            temperature=temperature,
        )

    else:
        raise ValueError("Unsupported LLM provider")

    LLM_CACHE[cache_key] = llm
    return llm


# This ensures the agent graph is compiled only once
def get_agent(llm, tools, enable_memory):

    cache_key = (
        llm.model_name,
        tuple(str(t) for t in tools),
        enable_memory,
    )

    if cache_key in AGENT_CACHE:
        return AGENT_CACHE[cache_key]

    if enable_memory:

        agent = create_react_agent(
            model=llm,
            tools=tools,
            checkpointer=memory,
        )

    else:

        agent = create_react_agent(
            model=llm,
            tools=tools,
        )

    AGENT_CACHE[cache_key] = agent
    return agent
