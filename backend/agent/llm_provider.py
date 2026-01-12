"""
Groq LLM provider with dynamic model selection.
"""

from functools import lru_cache

from langchain_groq import ChatGroq

from config import get_settings, AVAILABLE_MODELS, DEFAULT_MODEL


def get_llm(model_name: str | None = None, streaming: bool = False) -> ChatGroq:
    """
    Create a Groq LLM instance with the specified model.
    
    Args:
        model_name: The model identifier. Defaults to DEFAULT_MODEL.
        streaming: Whether to enable streaming responses.
        
    Returns:
        Configured ChatGroq instance.
    """
    settings = get_settings()
    
    # Use default if not specified or invalid
    if model_name is None:
        model_name = DEFAULT_MODEL
    elif not is_valid_model(model_name):
        model_name = DEFAULT_MODEL
    
    return ChatGroq(
        api_key=settings.groq_api_key,
        model_name=model_name,
        streaming=streaming,
        temperature=0.7,
        max_tokens=4096,
    )


def is_valid_model(model_name: str) -> bool:
    """Check if the model name is valid."""
    return any(m["id"] == model_name for m in AVAILABLE_MODELS)


def get_model_info(model_name: str) -> dict | None:
    """Get information about a specific model."""
    for model in AVAILABLE_MODELS:
        if model["id"] == model_name:
            return model
    return None


@lru_cache
def get_available_models() -> list[dict]:
    """Get list of all available models."""
    return AVAILABLE_MODELS.copy()
