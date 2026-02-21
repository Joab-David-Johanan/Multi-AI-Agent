import subprocess
import threading
import time
from dotenv import load_dotenv
from multi_agent_app.common.logger import get_logger
from multi_agent_app.common.custom_exception import CustomException

logger = get_logger(__name__)

load_dotenv()

# Note:
# backend host is 127.0.0.1
# backend runs on port 8000

# frontend host is 192.168.0.102
# frontend runs on port 8501


def run_backend():
    try:
        logger.info("starting backend service..")
        subprocess.run(
            [
                "uvicorn",
                "multi_agent_app.backend.api:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
            ],
            check=True,
        )
    except CustomException as e:
        logger.error("Problem with backend service")
        raise CustomException("Failed to start backend", e)


def run_frontend():
    try:
        logger.info("Starting Frontend service")
        subprocess.run(
            ["streamlit", "run", "multi_agent_app/frontend/main.py"], check=True
        )
    except CustomException as e:
        logger.error("Problem with frontend service")
        raise CustomException("Failed to start frontend", e)


if __name__ == "__main__":
    try:
        # starting the backend before the frontend
        threading.Thread(target=run_backend).start()
        time.sleep(2)
        run_frontend()

    except CustomException as e:
        logger.exception(f"CustomException occured : {str(e)}")
