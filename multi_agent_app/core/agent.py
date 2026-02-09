from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

from langchain.agents import create_agent
from langchain_core.messages.ai import AIMessage
from langchain_core.tools import tool

from langchain_community.tools.tavily_search import TavilySearchResults

from multi_agent_app.config.settings import settings


def generate_response(llm_model, query, allow_search):

    llm = ChatGroq(model=llm_model)
    web_results = [TavilySearchResults(max_results=2)] if allow_search else []

    agent = create_agent(
        model=llm,
        tools=[web_results],
        system_prompt=(
            "You are a research agent.\n"
            "- Use web_search and InternalResearchNotes to answer research questions.\n"
            "- Provide clear, factual, concise explanations.\n"
            "- Do NOT do arithmetic unless it is trivial."
        ),
    )

    # define the all messages with key 'messages'
    state = {"messages": query}

    # get the response from the llm based on the query
    response = agent.invoke(state)

    # contains both user queries and ai_messages
    messages = response.get("messages")

    # extracting all ai_messages
    ai_messages = [
        message.content for message in messages if isinstance(message, AIMessage)
    ]

    # return the latest ai_message
    return ai_messages[-1]
