import argparse
import os
import subprocess
import threading
import time
from dotenv import load_dotenv
from multi_agent_app.common.logger import get_logger
from multi_agent_app.common.custom_exception import CustomException

logger = get_logger(__name__)
load_dotenv()


# -----------------------------------
# Start Redis via Docker
# -----------------------------------
def start_redis():
    try:
        logger.info("Checking Redis Docker container...")

        # Check if container exists
        result = subprocess.run(
            [
                "docker",
                "ps",
                "-a",
                "--filter",
                "name=redis-cache",
                "--format",
                "{{.Names}}",
            ],
            capture_output=True,
            text=True,
        )

        if "redis-cache" in result.stdout:
            logger.info("Redis container exists. Starting...")
            subprocess.run(["docker", "start", "redis-cache"], check=True)
        else:
            logger.info("Creating new Redis container...")
            subprocess.run(
                [
                    "docker",
                    "run",
                    "-d",
                    "-p",
                    "6379:6379",
                    "--name",
                    "redis-cache",
                    "redis",
                ],
                check=True,
            )

        logger.info("Redis is running.")

    except Exception as e:
        logger.error("Failed to start Redis via Docker.")
        logger.error(str(e))


# -----------------------------------
# Backend
# -----------------------------------
def run_backend():
    try:
        logger.info("Starting backend service...")
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
    except Exception as e:
        logger.error("Problem with backend service")
        logger.error(str(e))


# -----------------------------------
# Streamlit Frontend
# -----------------------------------
def run_streamlit_frontend():
    try:
        logger.info("Starting Streamlit frontend service...")
        subprocess.run(
            ["streamlit", "run", "multi_agent_app/frontend/main.py"],
            check=True,
        )
    except Exception as e:
        logger.error("Problem with Streamlit frontend service")
        logger.error(str(e))


# -----------------------------------
# React Frontend
# -----------------------------------
def run_react_frontend():
    try:
        logger.info("Starting React frontend service...")
        npm_command = "npm.cmd" if os.name == "nt" else "npm"
        subprocess.run(
            [npm_command, "run", "dev", "--", "--host", "127.0.0.1"],
            cwd="multi_agent_app/react_frontend",
            check=True,
        )
    except Exception as e:
        logger.error("Problem with React frontend service")
        logger.error(str(e))


# -----------------------------------
# MAIN
# -----------------------------------
if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(
            description="Launch the AI agent app with Streamlit or React frontend."
        )
        parser.add_argument(
            "--frontend",
            choices=["streamlit", "react"],
            default="streamlit",
            help="Frontend to launch. Defaults to streamlit.",
        )
        args = parser.parse_args()

        # Start Redis
        start_redis()
        time.sleep(2)

        # Start Backend in Thread
        backend_thread = threading.Thread(target=run_backend)
        backend_thread.daemon = True
        backend_thread.start()

        time.sleep(3)

        # Start Frontend (main thread)
        if args.frontend == "react":
            run_react_frontend()
        else:
            run_streamlit_frontend()

    except Exception as e:
        logger.exception(f"Launcher error: {str(e)}")
