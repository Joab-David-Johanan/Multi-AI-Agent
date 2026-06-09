import json
import os
from datetime import datetime, timezone

import redis
from redis.exceptions import RedisError


EVALUATION_HISTORY_KEY = "evaluation:history"
ENABLE_REDIS_EVALUATIONS = os.getenv("ENABLE_REDIS_EVALUATIONS", "true").lower() == "true"

r = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=0,
    decode_responses=True,
    socket_connect_timeout=0.2,
    socket_timeout=0.2,
)

memory_runs = {}


def make_run_key(result: dict) -> str:
    model = result["model"]
    return (
        f"{model['llm_type']}:{model['model_name']}:"
        f"temperature-{model['temperature']}:search-{model['allow_search']}"
    )


def save_evaluation_run(result: dict) -> dict:
    run_key = make_run_key(result)
    saved_result = {
        **result,
        "run_id": run_key,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    if not ENABLE_REDIS_EVALUATIONS:
        memory_runs[run_key] = saved_result
        return saved_result

    try:
        r.hset(EVALUATION_HISTORY_KEY, run_key, json.dumps(saved_result))
    except RedisError:
        r.close()
        memory_runs[run_key] = saved_result

    return saved_result


def list_evaluation_runs() -> list[dict]:
    runs = []

    if not ENABLE_REDIS_EVALUATIONS:
        runs = list(memory_runs.values())
        return sorted(
            runs,
            key=lambda run: run.get("created_at", ""),
            reverse=True,
        )

    try:
        for raw_run in r.hvals(EVALUATION_HISTORY_KEY):
            runs.append(json.loads(raw_run))
    except RedisError:
        r.close()
        runs = list(memory_runs.values())

    return sorted(
        runs,
        key=lambda run: run.get("created_at", ""),
        reverse=True,
    )


def clear_evaluation_runs() -> int:
    if not ENABLE_REDIS_EVALUATIONS:
        count = len(memory_runs)
        memory_runs.clear()
        return count

    try:
        return r.delete(EVALUATION_HISTORY_KEY)
    except RedisError:
        r.close()
        count = len(memory_runs)
        memory_runs.clear()
        return count
