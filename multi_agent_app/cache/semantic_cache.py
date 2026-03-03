import numpy as np
from sentence_transformers import SentenceTransformer
from typing import Optional, Dict, Any

# ----------------------------
# Load embedding model once
# ----------------------------
model = SentenceTransformer("all-MiniLM-L6-v2")

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
#       "tool_enabled": bool
#   }
# }
semantic_store: Dict[str, Dict[str, Any]] = {}


# ----------------------------
# Utility functions
# ----------------------------
def get_embedding(text: str):
    """Generate embedding for text"""
    return model.encode(text)


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
    query: str, response: str, config: dict, tool_enabled: bool
):
    """Store query + response in semantic cache with context metadata"""
    emb = get_embedding(query)

    semantic_store[query] = {
        "embedding": emb,
        "response": response,
        "assistant_type": config["assistant_type"],
        "llm_type": config["llm_type"],
        "tool_enabled": tool_enabled,
    }


# ----------------------------
# Debug helper
# ----------------------------
def semantic_cache_size():
    return len(semantic_store)
