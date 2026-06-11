import time
from typing import Optional, Dict, Any

import numpy as np

# ----------------------------
# Load embedding model lazily
# ----------------------------
model = None


def get_model():
    global model

    if model is None:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer("all-MiniLM-L6-v2")

    return model

# similarity threshold (tune)
SIM_THRESHOLD = 0.88

# in-memory semantic cache store
# structure:
# {
#   "query": {
#       "embedding": np.array,
#       "response": str,
#       "assistant_type": str,
#       "llm_type": str,
#       "tool_enabled": bool,
#       "expires_at": float
#   }
# }
semantic_store: Dict[str, Dict[str, Any]] = {}


# ----------------------------
# Utility functions
# ----------------------------
def get_embedding(text: str):
    """Generate embedding for text"""
    return get_model().encode(text)


def cosine_similarity(a, b):
    """Compute cosine similarity"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


# ----------------------------
# Lookup
# ----------------------------
def semantic_lookup(query: str, config: dict, tool_enabled: bool) -> Optional[str]:
    """
    Check semantic cache for similar query.
    Respects assistant type, llm type, and tool usage.
    """

    if not semantic_store:
        return None

    query_emb = get_embedding(query)

    best_score = 0
    best_response = None

    for stored_query, data in semantic_store.items():

        # 🔒 Context isolation
        if data.get("expires_at", 0) <= time.time():
            continue

        if data["assistant_type"] != config["assistant_type"]:
            continue

        if data["llm_type"] != config["llm_type"]:
            continue

        if data["tool_enabled"] != tool_enabled:
            continue

        stored_emb = data["embedding"]
        score = cosine_similarity(query_emb, stored_emb)

        if score > best_score:
            best_score = score
            best_response = data["response"]

    if best_score >= SIM_THRESHOLD:
        return best_response

    return None


# ----------------------------
# Store
# ----------------------------
def semantic_store_response(
    query: str,
    response: str,
    config: dict,
    tool_enabled: bool,
    ttl_seconds: int = 3600,
):
    """Store query + response in semantic cache with context metadata"""
    emb = get_embedding(query)
    ttl_seconds = max(int(ttl_seconds or 3600), 1)

    semantic_store[query] = {
        "embedding": emb,
        "response": response,
        "assistant_type": config["assistant_type"],
        "llm_type": config["llm_type"],
        "tool_enabled": tool_enabled,
        "expires_at": time.time() + ttl_seconds,
    }


# ----------------------------
# Debug helper
# ----------------------------
def semantic_cache_size():
    return len(semantic_store)
