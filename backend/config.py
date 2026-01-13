"""
Configuration settings for T3.chat backend.
Uses pydantic-settings for environment variable management.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Groq API
    groq_api_key: str
    
    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "t3_chat"
    
    # LangSmith (optional)
    langsmith_api_key: str = ""
    langsmith_project: str = "t3-chat-clone"
    langsmith_tracing: str = "true"
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Available Groq Models
AVAILABLE_MODELS = [
    {
        "id": "llama-3.3-70b-versatile",
        "name": "Llama 3.3 70B Versatile",
        "description": "Meta's most capable open model, great for complex tasks",
        "context_length": 128000,
    },
    {
        "id": "llama-3.1-70b-versatile",
        "name": "Llama 3.1 70B Versatile",
        "description": "Powerful model for diverse applications",
        "context_length": 128000,
    },
    {
        "id": "llama-3.1-8b-instant",
        "name": "Llama 3.1 8B Instant",
        "description": "Fast and efficient for quick responses",
        "context_length": 128000,
    },
    {
        "id": "llama3-70b-8192",
        "name": "Llama 3 70B",
        "description": "High-quality responses with 8K context",
        "context_length": 8192,
    },
    {
        "id": "llama3-8b-8192",
        "name": "Llama 3 8B",
        "description": "Efficient model for everyday tasks",
        "context_length": 8192,
    },
    {
        "id": "mixtral-8x7b-32768",
        "name": "Mixtral 8x7B",
        "description": "Mixture of experts model with 32K context",
        "context_length": 32768,
    },
    {
        "id": "gemma2-9b-it",
        "name": "Gemma 2 9B",
        "description": "Google's efficient instruction-tuned model",
        "context_length": 8192,
    },
    {
        "id": "qwen-qwq-32b",
        "name": "Qwen QWQ 32B",
        "description": "Advanced reasoning model from Alibaba",
        "context_length": 32768,
    },
    {
        "id": "deepseek-r1-distill-llama-70b",
        "name": "DeepSeek R1 Distill 70B",
        "description": "Reasoning-focused distilled model",
        "context_length": 8192,
    },
]

DEFAULT_MODEL = "llama-3.3-70b-versatile"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
