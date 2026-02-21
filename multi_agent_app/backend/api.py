from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# import order matches code creation order
from multi_agent_app.common.logger import get_logger
from multi_agent_app.common.custom_exception import CustomException
from multi_agent_app.config.settings import settings
from multi_agent_app.core.agent import generate_response

logger = get_logger(__name__)

app = FastAPI(title="MULTI AI AGENT")


# Data model defining request structure from frontend
class RequestState(BaseModel):
    assistant_type: str
    llm_type: str
    model_name: str
    messages: list[str]
    temperature: float
    allow_search: bool
    streaming: bool


@app.post("/chat")
async def chat_endpoint(request: RequestState):

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

    # validate temperature values
    if request.temperature not in settings.ALLOWED_TEMPERATURE_VALUES:
        raise HTTPException(status_code=400, detail="Invalid temperature value")

    try:
        # Combine user messages into single query string
        query = "\n".join(request.messages)

        # Call async agent response
        response = await generate_response(
            request.assistant_type,
            request.llm_type,
            request.model_name,
            request.temperature,
            query,
            request.allow_search,
            False,  # never streams
        )

        return {"response": response}

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(CustomException("Failed to get AI response", error_detail=e)),
        )


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

    try:
        # Combine user messages into single query string
        query = "\n".join(request.messages)

        # Call async agent response for streaming
        return await generate_response(
            request.assistant_type,
            request.llm_type,
            request.model_name,
            request.temperature,
            query,
            request.allow_search,
            True,  # force streaming
        )

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(CustomException("Failed to get AI response", error_detail=e)),
        )
