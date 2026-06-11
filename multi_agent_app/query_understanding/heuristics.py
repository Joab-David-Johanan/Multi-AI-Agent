import re

from multi_agent_app.cache.cache_policy import TTL_POLICY
from multi_agent_app.query_understanding.models import (
    CacheDecision,
    QueryUnderstandingResult,
)


GREETING_OR_THANKS = {
    "hi",
    "hello",
    "hey",
    "hiya",
    "good morning",
    "good afternoon",
    "good evening",
    "thanks",
    "thank you",
    "thx",
    "ty",
}

CONTEXT_DEPENDENT_PATTERNS = [
    r"\bthis\b",
    r"\bthat\b",
    r"\bit\b",
    r"\babove\b",
    r"\bprevious\b",
    r"\bsecond one\b",
    r"\bfirst one\b",
    r"\bsame thing\b",
    r"\bdo that\b",
]

TRANSFORMATION_PATTERNS = [
    r"^explain (this|that|it)\b",
    r"^make (this|that|it) (shorter|longer|clearer|better|simple|simpler)\b",
    r"^summari[sz]e (this|that|it|the above)\b",
    r"^rewrite (this|that|it)\b",
    r"^improve (this|that|it)\b",
    r"^elaborate\b",
    r"^can you elaborate\b",
    r"^are you sure\b",
    r"^what are we talking about\b",
]

PROMPT_INJECTION_PATTERNS = [
    r"ignore (all )?(previous|prior|above) instructions",
    r"reveal (the )?(system|developer) prompt",
    r"show (the )?(system|developer) prompt",
    r"bypass (the )?(rules|policy|guardrails)",
    r"jailbreak",
]


def normalize_query(query: str) -> str:
    return " ".join(query.lower().strip().split())


def is_probably_gibberish(query: str) -> bool:
    normalized = normalize_query(query)

    if not normalized:
        return True

    alpha_chars = re.findall(r"[a-zA-Z]", normalized)
    if len(normalized) <= 2:
        return True

    if len(alpha_chars) < 3 and len(normalized) > 4:
        return True

    punctuation = re.findall(r"[^a-zA-Z0-9\s]", normalized)
    if punctuation and len(punctuation) / max(len(normalized), 1) > 0.45:
        return True

    long_token = max(normalized.split(), key=len, default="")
    vowels = len(re.findall(r"[aeiou]", long_token))
    if len(long_token) >= 12 and vowels <= 1:
        return True

    return False


def looks_compound(query: str) -> bool:
    normalized = normalize_query(query)
    return bool(
        re.search(r"\b(and|also|then)\b", normalized)
        or "," in normalized
        or ";" in normalized
    )


def infer_cache_category(query: str) -> str:
    normalized = normalize_query(query)

    if any(word in normalized for word in ["weather", "temperature", "forecast"]):
        return "weather"

    if any(word in normalized for word in ["stock", "share price", "market price"]):
        return "stock"

    if any(word in normalized for word in ["crypto", "bitcoin", "ethereum"]):
        return "crypto"

    if any(word in normalized for word in ["news", "headline", "latest"]):
        return "news"

    if re.search(r"\b(today|current|now|latest|live|real[- ]time)\b", normalized):
        return "unknown"

    if re.search(r"^(what is|define|explain|how does|why does|compare)\b", normalized):
        return "static"

    return "general"


def get_heuristic_cache_decision(query: str) -> QueryUnderstandingResult | None:
    normalized = normalize_query(query)

    if is_probably_gibberish(query):
        return _bypass(query, normalized, "malformed_or_gibberish", 0.95)

    if normalized in GREETING_OR_THANKS:
        return _bypass(query, normalized, "small_talk", 0.95)

    if any(re.search(pattern, normalized) for pattern in PROMPT_INJECTION_PATTERNS):
        return _bypass(query, normalized, "prompt_injection_or_policy_attack", 0.98)

    if any(re.search(pattern, normalized) for pattern in TRANSFORMATION_PATTERNS):
        return _bypass(query, normalized, "context_dependent_transformation", 0.96)

    if len(normalized.split()) <= 4 and any(
        re.search(pattern, normalized) for pattern in CONTEXT_DEPENDENT_PATTERNS
    ):
        return _bypass(query, normalized, "context_dependent_followup", 0.92)

    return None


def build_heuristic_cacheable_result(query: str) -> QueryUnderstandingResult:
    normalized = normalize_query(query)
    category = infer_cache_category(query)
    ttl_seconds = TTL_POLICY.get(category, TTL_POLICY["unknown"])

    return QueryUnderstandingResult(
        original_query=query,
        normalized_query=normalized,
        intent="standalone_or_general_query",
        is_compound=looks_compound(query),
        cache=CacheDecision(
            cacheable=True,
            reason="heuristic_cacheable_query",
            category=category,
            ttl_seconds=ttl_seconds,
            confidence=0.72,
        ),
        cache_strategy="global_cache",
        source="heuristic",
    )


def _bypass(
    query: str,
    normalized: str,
    reason: str,
    confidence: float,
) -> QueryUnderstandingResult:
    return QueryUnderstandingResult(
        original_query=query,
        normalized_query=normalized,
        intent=reason,
        cache=CacheDecision(
            cacheable=False,
            reason=reason,
            category="none",
            ttl_seconds=0,
            confidence=confidence,
        ),
        cache_strategy="bypass",
        source="heuristic",
    )
