from multi_agent_app.cache.exact_cache import exact_lookup, exact_store
from multi_agent_app.cache.semantic_cache import (
    semantic_lookup,
    semantic_store_response,
)


def check_cache(query, config, allow_search, history=None):
    # L1 exact cache
    res = exact_lookup(query, config)
    if res:
        return res, "exact"

    # L2 semantic cache (now context aware)
    res = semantic_lookup(query, config, allow_search)
    if res:
        return res, "semantic"

    return None, None


def store_all(query, response, config, allow_search):
    exact_store(query, response, config)
    semantic_store_response(query, response, config, allow_search)
