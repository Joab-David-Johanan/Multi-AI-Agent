import redis
import hashlib

r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)


def make_key(query, config):
    raw = f"{query}|{config['model_name']}|{config['temperature']}|{config.get('assistant_type')}|{config.get('llm_type')}"
    return hashlib.sha256(raw.encode()).hexdigest()


def exact_lookup(query, config):
    try:
        key = make_key(query, config)
        return r.get(key)
    except Exception:
        return None


def exact_store(query, response, config, ttl=3600):
    try:
        key = make_key(query, config)
        r.set(key, response, ex=ttl)
    except Exception:
        pass
