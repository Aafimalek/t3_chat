"""
Model listing endpoints.
"""

from fastapi import APIRouter

from models.schemas import ModelInfo
from config import AVAILABLE_MODELS, DEFAULT_MODEL

router = APIRouter(prefix="/api/models", tags=["Models"])


@router.get("", response_model=list[ModelInfo])
async def list_models() -> list[ModelInfo]:
    """List all available LLM models."""
    return [ModelInfo(**model) for model in AVAILABLE_MODELS]


@router.get("/default")
async def get_default_model() -> dict:
    """Get the default model information."""
    for model in AVAILABLE_MODELS:
        if model["id"] == DEFAULT_MODEL:
            return {
                "default_model": DEFAULT_MODEL,
                "info": ModelInfo(**model),
            }
    
    return {"default_model": DEFAULT_MODEL, "info": None}
