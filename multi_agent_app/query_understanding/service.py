from multi_agent_app.query_understanding.classifier import classify_query_with_llm
from multi_agent_app.query_understanding.decomposer import decompose_query
from multi_agent_app.query_understanding.heuristics import (
    build_heuristic_cacheable_result,
    get_heuristic_cache_decision,
)
from multi_agent_app.query_understanding.models import QueryUnderstandingResult


async def understand_query(query: str, request_context: dict | None = None) -> QueryUnderstandingResult:
    heuristic_result = get_heuristic_cache_decision(query)
    if heuristic_result:
        return heuristic_result

    try:
        result = await classify_query_with_llm(query)
    except Exception:
        result = build_heuristic_cacheable_result(query)
        result.source = "fallback"

    if result.is_compound:
        result.subqueries = decompose_query(query)
        if result.subqueries and result.cache.cacheable:
            result.cache_strategy = "subquery_cache"

    return result
