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
    
    # Tavily Search API
    tavily_api_key: str = ""
    
    # Ollama Embeddings
    ollama_base_url: str = "http://localhost:11434"
    ollama_embed_model: str = "nomic-embed-text"
    
    # RAG Configuration
    rag_chunk_size: int = 1000
    rag_chunk_overlap: int = 200
    rag_top_k: int = 5
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


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
