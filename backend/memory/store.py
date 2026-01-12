"""
MongoDB Store for long-term memory.
Stores persistent facts and user preferences across conversations.
"""

from functools import lru_cache

from langgraph.store.mongodb import MongoDBStore

from database import get_sync_client
from config import get_settings


@lru_cache
def get_memory_store() -> MongoDBStore:
    """
    Get the MongoDB store for long-term memory.
    
    The store persists information across conversations:
    - User preferences
    - Facts learned about the user
    - Important context from past interactions
    """
    client = get_sync_client()
    settings = get_settings()
    db = client[settings.database_name]
    
    return MongoDBStore(
        collection=db["memory_store"],
    )
