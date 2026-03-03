from multi_agent_app.cache.exact_cache import exact_lookup, exact_store
from multi_agent_app.cache.semantic_cache import (
    semantic_lookup,
    semantic_store_response,
)
from multi_agent_app.cache.tool_cache import tool_lookup, tool_store


def check_cache(query, config, history=None):
    res = exact_lookup(query, config)

    # L1 exact cache
    if res is not None:
        return res, "exact"

    # L2 semantic cache
    res = semantic_lookup(query)
    if res is not None:
        return res, "semantic"

    # L3 tool cache
    res = tool_lookup(query)
    if res is not None:
        return res, "tool"

    return None, None


def store_all(query, response, config, ttl):

    exact_store(query, response, config, ttl=ttl)
    semantic_store_response(query, response)
    tool_store(query, response)
