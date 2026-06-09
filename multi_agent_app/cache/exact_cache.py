import redis
import hashlib
import os

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
    raw = f"{query}|{config['model_name']}|{config['temperature']}|{config.get('assistant_type')}|{config.get('llm_type')}"
    return hashlib.sha256(raw.encode()).hexdigest()


def exact_lookup(query, config):
    key = make_key(query, config)

    if not ENABLE_REDIS_CACHE:
        return memory_store.get(key)

    try:
        return r.get(key)
    except RedisError:
        r.close()
        return memory_store.get(key)


def exact_store(query, response, config):
    key = make_key(query, config)

    if not ENABLE_REDIS_CACHE:
        memory_store[key] = response
        return

    try:
        r.set(key, response, ex=3600)  # 1h TTL
    except RedisError:
        r.close()
        memory_store[key] = response
