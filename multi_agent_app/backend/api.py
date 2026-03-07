import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Import order matches code creation order
# Logging and custom exception handling utilities
from multi_agent_app.common.logger import get_logger
from multi_agent_app.common.custom_exception import CustomException

# Application configuration (allowed models, assistants, temperature values)
from multi_agent_app.config.settings import settings

# Core AI agent responsible for generating responses
from multi_agent_app.core.agent import generate_response

# Backend caching system (exact cache + semantic cache)
from multi_agent_app.cache.cache_manager import check_cache, store_all

# Observability stack
# Prometheus collects metrics and Grafana visualizes them
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram

logger = get_logger(__name__)

# ---------------------------------------------------------
# FastAPI application instance
# ---------------------------------------------------------
app = FastAPI(title="MULTI AI AGENT")

# ---------------------------------------------------------
# Enable Prometheus metrics endpoint
# ---------------------------------------------------------
# This automatically exposes backend metrics at:
# http://127.0.0.1:8000/metrics
#
# Prometheus scrapes this endpoint and Grafana uses it
# to visualize traffic, latency and cache performance.
#
# The instrumentator also provides default HTTP metrics:
# - request count
# - request duration
# - response status codes
# ---------------------------------------------------------
Instrumentator().instrument(app).expose(app)


# ---------------------------------------------------------
# Custom metrics used for Grafana dashboards
# ---------------------------------------------------------

# Total number of requests processed by the backend
# Labels allow grouping by assistant type and model
REQUEST_COUNT = Counter(
    "ai_agent_requests_total",
    "Total requests",
    ["assistant", "model"],
)

# Total cache hits (exact cache or semantic cache)
CACHE_HITS = Counter(
    "ai_agent_cache_hits_total",
    "Cache hits",
    ["type"],
)

# Histogram measuring response latency of AI requests
# Prometheus automatically creates latency buckets
REQUEST_LATENCY = Histogram(
    "ai_agent_latency_seconds",
    "Latency of AI responses",
)

# Total number of backend errors
ERROR_COUNT = Counter(
    "ai_agent_errors_total",
    "Total errors",
)


# ---------------------------------------------------------
# Request model received from Streamlit frontend
# ---------------------------------------------------------
class RequestState(BaseModel):

    assistant_type: str
    llm_type: str
    model_name: str
    messages: list[str]

    temperature: float
    allow_search: bool
    streaming: bool

    # Thread identifier used by LangGraph conversational memory
    thread_id: str

    # Enable conversational memory
    enable_memory: bool = False

    # Enable backend caching (exact + semantic)
    enable_cache: bool = True


# ---------------------------------------------------------
# MAIN CHAT ENDPOINT (non-streaming responses)
# ---------------------------------------------------------
@app.post("/chat")
async def chat_endpoint(request: RequestState):

    logger.info(f"Assistant type: {request.assistant_type}")

    # ---------------------------------------------------------
    # Validate assistant type
    # Prevents invalid assistant requests
    # ---------------------------------------------------------
    if request.assistant_type not in settings.ASSISTANT_TYPES:
        raise HTTPException(status_code=400, detail="Invalid assistant type")

    logger.info(f"LLM Type: {request.llm_type}")

    # ---------------------------------------------------------
    # Validate LLM provider
    # Only supported providers are allowed
    # ---------------------------------------------------------
    if request.llm_type not in settings.ALLOWED_LLM_TYPES:
        raise HTTPException(status_code=400, detail="Invalid llm type")

    logger.info(f"Model Name: {request.model_name}")

    # ---------------------------------------------------------
    # Validate model name
    # Ensures only approved models are used
    # ---------------------------------------------------------
    if (
        request.model_name not in settings.ALLOWED_GROQ_MODEL_NAMES
        and request.model_name not in settings.ALLOWED_OPENAI_MODEL_NAMES
    ):
        raise HTTPException(status_code=400, detail="Invalid model name")

    # ---------------------------------------------------------
    # Validate temperature values
    # Prevents unsupported temperature ranges
    # ---------------------------------------------------------
    if request.temperature not in settings.ALLOWED_TEMPERATURE_VALUES:
        raise HTTPException(status_code=400, detail="Invalid temperature value")

    # ---------------------------------------------------------
    # METRIC: count incoming requests
    # Used by Grafana to show traffic per assistant/model
    # ---------------------------------------------------------
    REQUEST_COUNT.labels(
        assistant=request.assistant_type,
        model=request.model_name,
    ).inc()

    try:

        # Start latency timer for this request
        start_time = time.time()

        # ---------------------------------------------------------
        # Combine user messages into a single query string
        # ---------------------------------------------------------
        query = "\n".join(request.messages)

        # ---------------------------------------------------------
        # Build cache configuration
        # Prevents cross-assistant or cross-model cache pollution
        # ---------------------------------------------------------
        cache_config = {
            "model_name": request.model_name,
            "temperature": request.temperature,
            "assistant_type": request.assistant_type,
            "llm_type": request.llm_type,
        }

        # ---------------------------------------------------------
        # BACKEND CACHE CHECK
        # ---------------------------------------------------------
        # If caching is enabled we attempt:
        # 1) exact cache lookup
        # 2) semantic similarity cache lookup
        #
        # If a cached response exists we return immediately
        # without invoking the LLM.
        # ---------------------------------------------------------
        if request.enable_cache:

            cached_response, cache_type = check_cache(
                query,
                cache_config,
                request.allow_search,
            )

            if cached_response:

                # Record cache hit metric
                CACHE_HITS.labels(type=cache_type).inc()

                # Record latency for cached responses
                REQUEST_LATENCY.observe(time.time() - start_time)

                logger.info(f"Cache hit ({cache_type}) for query: {query[:60]}")

                return {
                    "response": cached_response,
                    "suggestions": [],
                    "cache": cache_type,
                }

        # ---------------------------------------------------------
        # Generate response using the AI agent
        # ---------------------------------------------------------
        result = await generate_response(
            request.assistant_type,
            request.llm_type,
            request.model_name,
            request.temperature,
            query,
            request.allow_search,
            False,  # never streams here
            request.thread_id,
            request.enable_memory,
        )

        # ---------------------------------------------------------
        # STORE RESPONSE IN CACHE
        # ---------------------------------------------------------
        if request.enable_cache and result and result != "Error":

            try:

                store_all(
                    query,
                    result["answer"],
                    cache_config,
                    request.allow_search,
                )

                logger.info("Stored response in cache")

            except Exception as cache_err:

                ERROR_COUNT.inc()
                logger.error(f"Cache store failed: {str(cache_err)}")

        # Record total request latency
        REQUEST_LATENCY.observe(time.time() - start_time)

        return {
            "response": result["answer"],
            "suggestions": result["suggestions"],
            "cache": "miss",
        }

    except Exception as e:

        ERROR_COUNT.inc()

        logger.error(f"Error: {str(e)}")

        raise HTTPException(
            status_code=500,
            detail=str(
                CustomException(
                    "Failed to get AI response",
                    error_detail=e,
                )
            ),
        )


# ---------------------------------------------------------
# STREAMING CHAT ENDPOINT
# Handles token streaming responses from the LLM
# ---------------------------------------------------------
@app.post("/chat-stream")
async def chat_stream_endpoint(request: RequestState):

    logger.info(f"Assistant type: {request.assistant_type}")

    # Validate assistant type
    if request.assistant_type not in settings.ASSISTANT_TYPES:
        raise HTTPException(status_code=400, detail="Invalid assistant type")

    logger.info(f"LLM Type: {request.llm_type}")

    # Validate LLM provider
    if request.llm_type not in settings.ALLOWED_LLM_TYPES:
        raise HTTPException(status_code=400, detail="Invalid llm type")

    logger.info(f"Model Name: {request.model_name}")

    # Validate model name
    if (
        request.model_name not in settings.ALLOWED_GROQ_MODEL_NAMES
        and request.model_name not in settings.ALLOWED_OPENAI_MODEL_NAMES
    ):
        raise HTTPException(status_code=400, detail="Invalid model name")

    # Count streaming requests as well
    REQUEST_COUNT.labels(
        assistant=request.assistant_type,
        model=request.model_name,
    ).inc()

    try:

        start_time = time.time()

        # Combine messages into a single query
        query = "\n".join(request.messages)

        # Generate streaming response
        response = await generate_response(
            request.assistant_type,
            request.llm_type,
            request.model_name,
            request.temperature,
            query,
            request.allow_search,
            True,  # force streaming
            request.thread_id,
            request.enable_memory,
        )

        # Record latency of streaming request
        REQUEST_LATENCY.observe(time.time() - start_time)

        return response

    except Exception as e:

        ERROR_COUNT.inc()

        logger.error(f"Error: {str(e)}")

        raise HTTPException(
            status_code=500,
            detail=str(
                CustomException(
                    "Failed to get AI response",
                    error_detail=e,
                )
            ),
        )
