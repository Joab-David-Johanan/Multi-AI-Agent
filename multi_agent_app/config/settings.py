from dotenv import load_dotenv
import os

load_dotenv()


class Settings:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

    ALLOWED_GROQ_MODEL_NAMES = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "qwen/qwen3-32b",
    ]

    ALLOWED_OPENAI_MODEL_NAMES = [
        "gpt-5-nano-2025-08-07",
        "gpt-4.1-nano-2025-04-14",
        "gpt-5-mini-2025-08-07",
    ]


settings = Settings()
