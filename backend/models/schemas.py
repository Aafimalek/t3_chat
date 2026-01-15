"""
Pydantic schemas for API requests and responses.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ============================================================================
# Message Schemas
# ============================================================================

class Message(BaseModel):
    """A single chat message."""
    
    role: Literal["user", "assistant", "system"] = Field(
        description="The role of the message sender"
    )
    content: str = Field(description="The message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Chat Schemas
# ============================================================================

class ChatRequest(BaseModel):
    """Request body for chat endpoint."""
    
    message: str = Field(description="The user's message")
    conversation_id: str | None = Field(
        default=None,
        description="Optional conversation ID to continue a conversation"
    )
    model_name: str | None = Field(
        default=None,
        description="Optional model to use for this request"
    )
    user_id: str = Field(description="User identifier")
    tool_mode: Literal["auto", "search", "none"] = Field(
        default="auto",
        description="Tool mode: 'auto' for heuristic detection, 'search' to force search, 'none' to disable"
    )
    use_rag: bool = Field(
        default=True,
        description="Whether to use RAG if documents are available"
    )


class ChatResponse(BaseModel):
    """Response body for chat endpoint."""
    
    response: str = Field(description="The assistant's response")
    conversation_id: str = Field(description="The conversation ID")
    model_used: str = Field(description="The model that generated the response")


# ============================================================================
# Conversation Schemas
# ============================================================================

class ConversationSummary(BaseModel):
    """Summary of a conversation for listing."""
    
    id: str = Field(description="Unique conversation identifier")
    title: str = Field(description="Conversation title")
    model_name: str = Field(description="Model used in conversation")
    created_at: datetime
    updated_at: datetime
    message_count: int = Field(default=0)


class Conversation(BaseModel):
    """Full conversation with messages."""
    
    id: str = Field(description="Unique conversation identifier")
    user_id: str = Field(description="Owner of the conversation")
    title: str = Field(description="Conversation title")
    model_name: str = Field(description="Model used in conversation")
    messages: list[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ConversationUpdate(BaseModel):
    """Request body for updating a conversation."""
    
    title: str | None = Field(default=None, description="New title")


# ============================================================================
# Model Schemas
# ============================================================================

class ModelInfo(BaseModel):
    """Information about an available LLM model."""
    
    id: str = Field(description="Model identifier for API calls")
    name: str = Field(description="Human-readable model name")
    description: str = Field(description="Brief description of the model")
    context_length: int = Field(description="Maximum context window size")
