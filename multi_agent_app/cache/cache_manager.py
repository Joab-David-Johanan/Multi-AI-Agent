import os

from multi_agent_app.cache.exact_cache import exact_lookup, exact_store
from multi_agent_app.cache.semantic_cache import (
    semantic_lookup,
    semantic_store_response,
)

ENABLE_SEMANTIC_CACHE = os.getenv("ENABLE_SEMANTIC_CACHE", "false").lower() == "true"


def check_cache(query, config, allow_search, understanding=None, history=None):
    if understanding and not understanding.cache.cacheable:
        return None, None

    # L1 exact cache
    res = exact_lookup(query, config)
    if res:
        return res, "exact"

    if not ENABLE_SEMANTIC_CACHE:
        return None, None

    # L2 semantic cache (now context aware)
    res = semantic_lookup(query, config, allow_search)
    if res:
        return res, "semantic"

    return None, None


def store_all(query, response, config, allow_search, understanding=None):
    if understanding and not understanding.cache.cacheable:
        return False

    ttl_seconds = 3600
    if understanding:
        ttl_seconds = understanding.cache.ttl_seconds or ttl_seconds

    exact_store(query, response, config, ttl_seconds)

    if ENABLE_SEMANTIC_CACHE:
        semantic_store_response(query, response, config, allow_search, ttl_seconds)

    return True
