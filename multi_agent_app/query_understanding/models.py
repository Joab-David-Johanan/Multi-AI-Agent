from typing import Literal

from pydantic import BaseModel, Field


CacheCategory = Literal[
    "weather",
    "news",
    "crypto",
    "stock",
    "static",
    "general",
    "none",
    "unknown",
]

CacheStrategy = Literal["global_cache", "subquery_cache", "bypass"]


class CacheDecision(BaseModel):
    cacheable: bool = False
    reason: str = "low_confidence"
    category: CacheCategory = "none"
    ttl_seconds: int = 0
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class RoutingDecision(BaseModel):
    requires_tools: bool = False
    recommended_tools: list[str] = Field(default_factory=list)


class SubQuery(BaseModel):
    text: str
    intent: str = "unknown"
    cache: CacheDecision = Field(default_factory=CacheDecision)
    routing: RoutingDecision = Field(default_factory=RoutingDecision)


class QueryUnderstandingResult(BaseModel):
    original_query: str
    normalized_query: str
    intent: str = "unknown"
    is_compound: bool = False
    subqueries: list[SubQuery] = Field(default_factory=list)
    cache: CacheDecision = Field(default_factory=CacheDecision)
    routing: RoutingDecision = Field(default_factory=RoutingDecision)
    cache_strategy: CacheStrategy = "bypass"
    source: Literal["heuristic", "llm", "fallback"] = "fallback"
