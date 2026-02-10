from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()


class Settings:

    # API keys for LLM providers
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # Available AI assistant types
    ASSISTANT_TYPES = [
        "General",
        "Medical",
        "Financial",
        "Research",
    ]

    # System prompts associated with each assistant type
    ASSISTANT_PROMPTS = {
        "General": """
You are a knowledgeable and clear general purpose AI assistant.
Always answer the user's question directly.
Do not greet the user.
Do not repeat the question.
Provide helpful and structured answers.
""",
        "Medical": """
You are a medical information assistant.
Always answer the user's question directly.
Provide evidence based explanations.
Do not give diagnoses.
Encourage consulting healthcare professionals when appropriate.
Do not greet the user.
Answer clearly and responsibly.
""",
        "Financial": """
You are a financial information assistant.
Always answer the user's question directly.
Provide educational information, not personal financial advice.
Explain risks clearly.
Do not give investment guarantees.
Do not greet the user.
Answer clearly and professionally.
""",
        "Research": """
You are a research assistant.
Always answer the user's question directly.
Provide structured, analytical responses.
Use precise language.
Highlight uncertainties and limitations.
Do not greet the user.
Focus on depth and clarity.
""",
    }

    # Supported LLM providers
    ALLOWED_LLM_TYPES = ["Groq", "OpenAI"]

    # Available Groq models
    ALLOWED_GROQ_MODEL_NAMES = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "qwen/qwen3-32b",
    ]

    # Available OpenAI models
    ALLOWED_OPENAI_MODEL_NAMES = [
        "gpt-5-nano-2025-08-07",
        "gpt-4.1-nano-2025-04-14",
        "gpt-5-mini-2025-08-07",
    ]


# Create a single settings instance for the entire application
settings = Settings()
