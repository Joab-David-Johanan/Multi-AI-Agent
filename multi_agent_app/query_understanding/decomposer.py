import re

from multi_agent_app.cache.cache_policy import TTL_POLICY
from multi_agent_app.query_understanding.heuristics import infer_cache_category
from multi_agent_app.query_understanding.models import CacheDecision, SubQuery


def decompose_query(query: str) -> list[SubQuery]:
    parts = [
        part.strip(" ,;")
        for part in re.split(r"\b(?:and|also|then)\b|[;]", query, flags=re.IGNORECASE)
        if part.strip(" ,;")
    ]

    if len(parts) <= 1:
        return []

    subqueries = []
    for part in parts:
        category = infer_cache_category(part)
        subqueries.append(
            SubQuery(
                text=part,
                intent="subquery",
                cache=CacheDecision(
                    cacheable=True,
                    reason="decomposed_cacheable_subquery",
                    category=category,
                    ttl_seconds=TTL_POLICY.get(category, TTL_POLICY["unknown"]),
                    confidence=0.65,
                ),
            )
        )

    return subqueries
