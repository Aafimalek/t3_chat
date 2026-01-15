"""
Configuration settings for T3.chat backend.
Uses pydantic-settings for environment variable management.
"""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Explicitly load .env file from the backend directory
_backend_dir = Path(__file__).parent
_env_file = _backend_dir / ".env"
load_dotenv(_env_file)

# Debug: Print to verify env loading (remove after testing)
import sys
print(f"[Config] Loading .env from: {_env_file}", flush=True)
print(f"[Config] TAVILY_API_KEY loaded: {'Yes' if os.getenv('TAVILY_API_KEY') else 'No'}", flush=True)
sys.stdout.flush()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Groq API
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    
    # MongoDB (Atlas)
    mongodb_url: str = os.getenv("MONGODB_URL")
    database_name: str = os.getenv("DATABASE_NAME", "t3_chat")
    
    # LangSmith (optional)
    langsmith_api_key: str = os.getenv("LANGSMITH_API_KEY", "")
    langsmith_project: str = os.getenv("LANGSMITH_PROJECT", "t3-chat-clone")
    langsmith_tracing: str = os.getenv("LANGSMITH_TRACING", "true")
    langsmith_endpoint: str = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    
    # Tavily Search API
    tavily_api_key: str = os.getenv("TAVILY_API_KEY", "")
    
    # Ollama Embeddings
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_embed_model: str = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
    
    # RAG Configuration
    rag_chunk_size: int = int(os.getenv("RAG_CHUNK_SIZE", "1000"))
    rag_chunk_overlap: int = int(os.getenv("RAG_CHUNK_OVERLAP", "200"))
    rag_top_k: int = int(os.getenv("RAG_TOP_K", "5"))
    
    # CORS Configuration
    # Comma-separated list of allowed origins, or "*" for all (not recommended with credentials)
    cors_origins: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173"
    )
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins into a list."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
    
    # Pydantic v2 configuration
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",  # Ignore extra fields from .env file
    }


# Available Groq Models
AVAILABLE_MODELS = [
    {
        "id": "qwen/qwen3-32b",
        "name": "Qwen 3 32B",
        "description": "Qwen 3 32B Model",
        "context_length": 32768,
    },
    {
        "id": "groq/compound",
        "name": "Groq Compound",
        "description": "Groq Compound Model",
        "context_length": 8192,
    },
    {
        "id": "meta-llama/llama-4-maverick-17b-128e-instruct",
        "name": "Llama 4 Maverick",
        "description": "Llama 4 Maverick 17B",
        "context_length": 128000,
    },
    {
        "id": "meta-llama/llama-4-scout-17b-16e-instruct",
        "name": "Llama 4 Scout",
        "description": "Llama 4 Scout 17B",
        "context_length": 128000,
    },
    {
        "id": "moonshotai/kimi-k2-instruct-0905",
        "name": "Kimi K2",
        "description": "Moonshot AI Kimi K2",
        "context_length": 128000,
    },
    {
        "id": "openai/gpt-oss-120b",
        "name": "GPT OSS 120B",
        "description": "OpenAI GPT OSS 120B",
        "context_length": 128000,
    },
    {
        "id": "llama-3.1-8b-instant",
        "name": "Llama 3.1 8B Instant",
        "description": "Fast and efficient Llama 3.1 8B model",
        "context_length": 128000,
    },
    {
        "id": "llama-3.3-70b-versatile",
        "name": "Llama 3.3 70B Versatile",
        "description": "Versatile Llama 3.3 70B model",
        "context_length": 128000,
    },
]

DEFAULT_MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
