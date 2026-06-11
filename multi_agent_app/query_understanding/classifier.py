import json
import re

from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq

from multi_agent_app.cache.cache_policy import TTL_POLICY
from multi_agent_app.query_understanding.models import (
    CacheDecision,
    QueryUnderstandingResult,
    RoutingDecision,
)
from multi_agent_app.query_understanding.prompts import QUERY_CLASSIFIER_PROMPT
from multi_agent_app.query_understanding.heuristics import normalize_query

VALID_CATEGORIES = set(TTL_POLICY.keys()) | {"none"}


async def classify_query_with_llm(query: str) -> QueryUnderstandingResult:
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0,
    )

    response = await llm.ainvoke(
        [HumanMessage(content=f"{QUERY_CLASSIFIER_PROMPT}\n\nQuery: {query}")]
    )

    payload = _parse_json(response.content)
    category = str(payload.get("category", "unknown")).lower()
    if category not in VALID_CATEGORIES:
        category = "unknown"

    cacheable = bool(payload.get("cacheable", False))
    if not cacheable:
        category = "none"

    ttl_seconds = TTL_POLICY.get(category, 0 if category == "none" else TTL_POLICY["unknown"])

    return QueryUnderstandingResult(
        original_query=query,
        normalized_query=normalize_query(query),
        intent=str(payload.get("intent", "unknown")).lower(),
        is_compound=bool(payload.get("is_compound", False)),
        cache=CacheDecision(
            cacheable=cacheable,
            reason=str(payload.get("reason", "low_confidence")).lower(),
            category=category,
            ttl_seconds=ttl_seconds,
            confidence=float(payload.get("confidence", 0.0)),
        ),
        routing=RoutingDecision(
            requires_tools=bool(payload.get("requires_tools", False)),
            recommended_tools=list(payload.get("recommended_tools", [])),
        ),
        cache_strategy="global_cache" if cacheable else "bypass",
        source="llm",
    )


def _parse_json(content: str) -> dict:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


async def classify_query(query: str) -> str:
    result = await classify_query_with_llm(query)
    return result.cache.category
