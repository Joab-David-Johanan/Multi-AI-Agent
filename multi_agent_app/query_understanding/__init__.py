from multi_agent_app.query_understanding.heuristics import get_heuristic_cache_decision


async def understand_query(query: str, request_context: dict | None = None):
    from multi_agent_app.query_understanding.service import understand_query as _understand

    return await _understand(query, request_context)


__all__ = ["understand_query", "get_heuristic_cache_decision"]
