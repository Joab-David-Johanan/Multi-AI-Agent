import redis
import hashlib
import os

r = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=0,
    decode_responses=True,
)


def make_key(query, config):
    raw = f"{query}|{config['model_name']}|{config['temperature']}|{config.get('assistant_type')}|{config.get('llm_type')}"
    return hashlib.sha256(raw.encode()).hexdigest()


def exact_lookup(query, config):
    key = make_key(query, config)
    return r.get(key)


def exact_store(query, response, config):
    key = make_key(query, config)
    r.set(key, response, ex=3600)  # 1h TTL
