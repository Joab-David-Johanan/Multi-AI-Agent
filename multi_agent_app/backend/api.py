from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from multi_agent_app.core.agent import generate_response
from multi_agent_app.config.settings import settings
from multi_agent_app.common.logger import get_logger
from multi_agent_app.common.custom_exception import CustomException

# intializing the logger
logger = get_logger(__name__)

# intialize fastapi
app = FastAPI(title="MULTI AI AGENT")


# data validation using pydantic
class RequestState(BaseModel):
    model_name: str
    messages: list[str]
    allow_search: bool
    system_prompt: str


@app.post("/chat")
async def chat_endpoint(request: RequestState):
    logger.info(f"Received request for model: {request.model_name}")

    if (
        request.model_name not in settings.ALLOWED_GROQ_MODEL_NAMES
        and settings.ALLOWED_OPENAI_MODEL_NAMES
    ):
        logger.warning("Invalid model name")
        raise HTTPException(status_code=400, detail="Invalid model name")

    try:
        response = generate_response(
            request.model_name,
            request.messages,
            request.allow_search,
            request.system_prompt,
        )

        logger.info(f"Successfully got response from AI Agent {request.model_name}")

        return {"response": response}

    except Exception as e:
        logger.error("Some error occured during response generation")
        raise HTTPException(
            status_code=500,
            detail=str(CustomException("Failed to get AI response", error_detail=e)),
        )
