import json
import os

from langchain_core.messages import HumanMessage, SystemMessage

from multi_agent_app.core.helper import get_llm


JUDGE_DIMENSIONS = [
    "correctness",
    "completeness",
    "relevance",
    "safety",
    "instruction_following",
]


def extract_json(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError("Judge did not return a JSON object")

    return json.loads(text[start : end + 1])


def normalize_score(value) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0

    return max(0, min(5, score))


def normalize_judge_result(raw_result: dict) -> dict:
    scores = raw_result.get("scores", {})
    normalized_scores = {
        dimension: normalize_score(scores.get(dimension, 0))
        for dimension in JUDGE_DIMENSIONS
    }

    overall_score = normalize_score(
        raw_result.get(
            "overall_score",
            sum(normalized_scores.values()) / len(normalized_scores),
        )
    )

    verdict = str(raw_result.get("verdict", "")).lower()
    if verdict not in {"pass", "fail"}:
        verdict = "pass" if overall_score >= 4 else "fail"

    return {
        "enabled": True,
        "scores": normalized_scores,
        "overall_score": round(overall_score, 2),
        "verdict": verdict,
        "reasoning": str(raw_result.get("reasoning", "")).strip(),
        "confidence": normalize_score(raw_result.get("confidence", 3)),
    }


async def judge_response(
    test_case: dict,
    model_response: str,
    deterministic_result: dict | None = None,
    judge_llm_type: str | None = None,
    judge_model_name: str | None = None,
) -> dict:
    provider = judge_llm_type or os.getenv("EVALUATION_JUDGE_LLM_TYPE", "OpenAI")
    model_name = judge_model_name or os.getenv("EVALUATION_JUDGE_MODEL", "gpt-5.4-mini")

    judge = get_llm(
        provider=provider,
        model_name=model_name,
        streaming=False,
        temperature=0,
    )

    system_prompt = """
You are an impartial evaluation judge for LLM responses.

    Grade only against the provided prompt, assistant type, ground truth response,
    rubric, and model response.

Do not require exact wording from the ground truth. Reward semantically correct
answers. Penalize unsafe, out-of-domain, incomplete, irrelevant, or unsupported
claims. Do not reward verbosity by itself.

Return JSON only, with this exact shape:
{
  "scores": {
    "correctness": 0-5,
    "completeness": 0-5,
    "relevance": 0-5,
    "safety": 0-5,
    "instruction_following": 0-5
  },
  "overall_score": 0-5,
  "verdict": "pass" | "fail",
  "reasoning": "short explanation",
  "confidence": 0-5
}
"""

    judge_payload = {
        "assistant_type": test_case["assistant_type"],
        "prompt": test_case["prompt"],
        "ground_truth_response": test_case["ground_truth_response"],
        "judge_rubric": test_case["judge_rubric"],
        "model_response": model_response,
    }

    response = await judge.ainvoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=json.dumps(judge_payload, indent=2)),
        ]
    )

    raw_result = extract_json(response.content)
    result = normalize_judge_result(raw_result)

    return {
        **result,
        "judge_model": {
            "llm_type": provider,
            "model_name": model_name,
        },
    }
