"""
MongoDB Checkpointer for short-term memory.
Stores LangGraph state snapshots for conversation continuity.
"""

from functools import lru_cache

from langgraph.checkpoint.mongodb import MongoDBSaver

from database import get_sync_client
from config import get_settings


@lru_cache
def get_checkpointer() -> MongoDBSaver:
    """
    Get the MongoDB checkpointer for short-term memory.
    
    The checkpointer stores graph state at each step, enabling:
    - Conversation continuity across requests
    - Time travel through conversation history
    - Fault tolerance and recovery
    """
    client = get_sync_client()
    settings = get_settings()
    
    return MongoDBSaver(
        client=client,
        db_name=settings.database_name,
    )
