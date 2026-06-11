import redis
import hashlib
import os
import time

from redis.exceptions import RedisError

ENABLE_REDIS_CACHE = os.getenv("ENABLE_REDIS_CACHE", "true").lower() == "true"

r = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=0,
    decode_responses=True,
    socket_connect_timeout=0.2,
    socket_timeout=0.2,
)

memory_store = {}


def make_key(query, config):
    raw = (
        f"{query}|{config['model_name']}|{config['temperature']}|"
        f"{config.get('assistant_type')}|{config.get('llm_type')}|"
        f"{config.get('allow_search')}"
    )
    return hashlib.sha256(raw.encode()).hexdigest()


def exact_lookup(query, config):
    key = make_key(query, config)

    if not ENABLE_REDIS_CACHE:
        return memory_lookup(key)

    try:
        return r.get(key)
    except RedisError:
        r.close()
        return memory_lookup(key)


def exact_store(query, response, config, ttl_seconds=3600):
    key = make_key(query, config)
    ttl_seconds = max(int(ttl_seconds or 3600), 1)

    if not ENABLE_REDIS_CACHE:
        memory_store[key] = (response, time.time() + ttl_seconds)
        return

    try:
        r.set(key, response, ex=ttl_seconds)
    except RedisError:
        r.close()
        memory_store[key] = (response, time.time() + ttl_seconds)


def memory_lookup(key):
    cached = memory_store.get(key)
    if not cached:
        return None

    if isinstance(cached, tuple):
        response, expires_at = cached
        if expires_at <= time.time():
            memory_store.pop(key, None)
            return None
        return response

    return cached
