# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Install the package in editable mode (pulls deps from `pyproject.toml`):
```bash
pip install -e .
pip install -r requirements.txt   # pins additional runtime deps not in pyproject
```

Run the full stack (Redis container + FastAPI on 8000 + Streamlit on 8501):
```bash
python multi_agent_app/launcher.py
```

Run components individually for development:
```bash
uvicorn multi_agent_app.backend.api:app --host 127.0.0.1 --port 8000 --reload
streamlit run multi_agent_app/frontend/main.py
```

Observability stack (from `docker commands.txt`):
```bash
MSYS_NO_PATHCONV=1 docker run -d -p 9090:9090 --name prometheus \
  -v /c/Coding/Projects/AI_agent_app/prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus
docker run -d -p 3000:3000 --name grafana -e GF_SECURITY_ALLOW_EMBEDDING=true grafana/grafana
```
Prometheus is configured to scrape `host.docker.internal:8000/metrics` — the backend must be reachable from the Prometheus container. Grafana's `GF_SECURITY_ALLOW_EMBEDDING=true` is required because Streamlit embeds the dashboard in an iframe.

**No test suite exists** despite `pytest` being declared as a dev dep in `pyproject.toml`. Lint tooling (`black`, `ruff`) is declared but not wired into CI.

### Known stale references
- `README.md` and `Dockerfile` both instruct `python multi_agent_app/main.py`, but the entrypoint was renamed to `launcher.py` (see commit `9515d1a`). The Dockerfile `CMD` will fail as written.
- `BACKEND_URL` is hardcoded to `http://127.0.0.1:8000/chat` in [chat_handler.py:10](multi_agent_app/frontend/chat_handler.py#L10) — breaks in containerized deployments.

## Architecture

### Process topology
`launcher.py` is the orchestrator. It spawns three things in order: (1) a Redis container named `redis-cache` via `docker run`/`docker start`, (2) the FastAPI backend in a daemon thread, (3) the Streamlit frontend on the main thread. Frontend → backend communication is plain HTTP over `127.0.0.1:8000`. The Redis container is started but **semantic cache currently uses an in-memory dict in the Python process**, not Redis — Redis is provisioned for future use.

### Request flow (`POST /chat`)
1. [backend/api.py](multi_agent_app/backend/api.py) validates the payload against allowlists in [config/settings.py](multi_agent_app/config/settings.py) (assistant type, LLM provider, model, temperature).
2. [cache/cache_manager.py](multi_agent_app/cache/cache_manager.py) runs a two-tier lookup: L1 exact string match → L2 semantic (cosine similarity over `all-MiniLM-L6-v2` embeddings, threshold `0.88`). Cache keys are **context-isolated** by `(assistant_type, llm_type, tool_enabled)` — a "Medical" hit will never serve a "Financial" query even if the text matches.
3. On miss, [core/agent.py](multi_agent_app/core/agent.py) `generate_response` assembles a system prompt (`BASE_SYSTEM_PROMPT` + assistant-specific prompt from settings), builds state, and invokes a LangGraph ReAct agent.
4. Response is parsed for the structured contract `ANSWER:\n...\nSUGGESTIONS:\n1. ...\n2. ...\n3. ...` — both the system prompt and the parser in `agent.py` depend on this exact format. Changes to one must match the other.
5. Successful responses are stored in both cache layers via `store_all`.

### LLM / agent lifecycle
[core/helper.py](multi_agent_app/core/helper.py) holds three module-level dicts: `LLM_CACHE`, `AGENT_CACHE`, `TOOL_CACHE`. `get_llm` is keyed by `(provider, model_name, streaming, temperature)`; `get_agent` is keyed by `(model_name, tuple(tools), enable_memory)`. Any change in any key field triggers recreation. The LangGraph `MemorySaver` checkpoint is a single module-level instance shared across all memory-enabled agents — conversations are isolated by `thread_id` in the `config={"configurable": {"thread_id": ...}}` param, not by separate checkpointers.

### Search-tool heuristic
In [agent.py:41-53](multi_agent_app/core/agent.py#L41-L53), the Tavily tool is stripped from the agent when the query starts with `"what is"`, `"define"`, or `"explain"` — **unless** it contains `"price"`, `"now"`, `"current"`, or `"today"`. This is a deliberate cost/latency optimization: basic knowledge questions shouldn't trigger web search. When modifying agent behavior, remember the tool list is decided per-request before `get_agent` is called, so the cache key differs for search-on vs search-off variants.

### "Streaming" is fake
The `/chat-stream` endpoint does **not** use true token streaming. It awaits the full agent response, then yields it character-by-character with `asyncio.sleep(0.01)` in [agent.py:125-130](multi_agent_app/core/agent.py#L125-L130). When working on streaming, don't assume mid-generation cancellation or real-time token delivery.

### Three cache layers (not two)
Separate from the backend's L1/L2, the Streamlit frontend maintains its own **session cache** in `st.session_state.cache_store`, keyed by `(assistant_type, llm_type, model, temperature, user_input)`. Session cache is consulted *before* hitting the backend and is displayed as a distinct mode ("Session cache hit") in the UI. All three layers can be independently toggled from the sidebar.

### Configuration surface
[config/settings.py](multi_agent_app/config/settings.py) is the single source of truth for: API keys (via dotenv), the 4 assistant types and their system prompts, allowed LLM providers/models, and the allowed temperature values (0.0–1.0 in 0.1 steps). Adding a new assistant type requires only adding an entry to `ASSISTANT_TYPES` and `ASSISTANT_PROMPTS` — it will automatically appear in the sidebar dropdown and be accepted by the backend validator.

### Prometheus metrics
[backend/api.py](multi_agent_app/backend/api.py) registers four custom metrics alongside the default `Instrumentator()` HTTP metrics: `ai_agent_requests_total` (labeled by `assistant`, `model`), `ai_agent_cache_hits_total` (labeled by `type` = exact/semantic), `ai_agent_latency_seconds` (histogram), `ai_agent_errors_total`. New metrics should follow the `ai_agent_*` prefix for Grafana dashboard consistency.

### Typo convention
The variable `enable_coversational_memory` (missing `n`) is used consistently across frontend files. Preserve the typo when editing — don't "fix" it in isolation or you'll break the prop chain between [sidebar_ui.py](multi_agent_app/frontend/sidebar_ui.py), [chat_handler.py](multi_agent_app/frontend/chat_handler.py), and [main.py](multi_agent_app/frontend/main.py).
