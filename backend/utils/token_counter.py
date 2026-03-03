"""
Token counting utilities for context window management and usage tracking.

Uses tiktoken with cl100k_base encoding as a reasonable approximation
for Llama/Qwen/Groq models (within ~5% accuracy).
"""

from functools import lru_cache

import tiktoken

from config import AVAILABLE_MODELS, get_settings


@lru_cache
def _get_encoding():
    """Get the tiktoken encoding (cached)."""
    return tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """Count tokens in a text string."""
    if not text:
        return 0
    enc = _get_encoding()
    return len(enc.encode(text))


def count_messages_tokens(messages: list) -> int:
    """
    Count total tokens across a list of LangChain BaseMessage objects.
    
    Accounts for message overhead (~4 tokens per message for role/formatting).
    """
    total = 0
    for msg in messages:
        content = msg.content if hasattr(msg, "content") else str(msg)
        # ~4 tokens overhead per message (role, delimiters)
        total += count_tokens(content) + 4
    return total


def get_model_context_length(model_name: str) -> int:
    """Look up the context window size for a model."""
    for model in AVAILABLE_MODELS:
        if model["id"] == model_name:
            return model["context_length"]
    # Default fallback
    return 128000


def get_context_budget(model_name: str) -> int:
    """
    Calculate the usable token budget for input messages.
    
    Formula: context_length - max_output_tokens - safety_margin
    """
    settings = get_settings()
    context_length = get_model_context_length(model_name)
    budget = context_length - settings.max_output_tokens - settings.context_reserve_tokens
    return max(budget, 2048)  # Never go below 2048 usable tokens
