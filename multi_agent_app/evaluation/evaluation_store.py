import json
import os
from datetime import datetime, timezone

import redis


EVALUATION_HISTORY_KEY = "evaluation:history"

r = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=0,
    decode_responses=True,
)


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

    r.hset(EVALUATION_HISTORY_KEY, run_key, json.dumps(saved_result))
    return saved_result


def list_evaluation_runs() -> list[dict]:
    runs = []

    for raw_run in r.hvals(EVALUATION_HISTORY_KEY):
        runs.append(json.loads(raw_run))

    return sorted(
        runs,
        key=lambda run: run.get("created_at", ""),
        reverse=True,
    )


def clear_evaluation_runs() -> int:
    return r.delete(EVALUATION_HISTORY_KEY)
