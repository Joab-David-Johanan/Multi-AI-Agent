tool_cache = {}


def tool_lookup(query):
    return tool_cache.get(query)


def tool_store(query, result):
    tool_cache[query] = result
