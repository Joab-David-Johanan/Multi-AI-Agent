from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

CLASSIFIER_PROMPT = """
Classify the query into exactly one word:
weather, news, crypto, stock, static, general.
Return only the word.
"""


async def classify_query(query: str) -> str:
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0,
    )

    response = await llm.ainvoke(
        [HumanMessage(content=CLASSIFIER_PROMPT + "\n\nQuery: " + query)]
    )

    return response.content.strip().lower()
