"""
MongoDB Store for long-term memory.
Stores persistent facts and user preferences across conversations.
"""

from langgraph.store.mongodb import MongoDBStore

from database import get_sync_client
from config import get_settings


# Cache the store instance but with validation
_memory_store: MongoDBStore | None = None


def get_memory_store() -> MongoDBStore:
    """
    Get the MongoDB store for long-term memory.
    
    The store persists information across conversations:
    - User preferences
    - Facts learned about the user
    - Important context from past interactions
    """
    global _memory_store
    
    # Always get a fresh client reference to handle reconnection
    client = get_sync_client()
    settings = get_settings()
    
    # Validate connection is alive
    try:
        client.admin.command('ping')
    except Exception as e:
        print(f"[MemoryStore] Connection ping failed, will reconnect: {e}", flush=True)
        # Force reconnection by clearing the global client
        from database import _sync_client
        import database
        if database._sync_client is not None:
            try:
                database._sync_client.close()
            except:
                pass
            database._sync_client = None
        client = get_sync_client()
        _memory_store = None  # Force recreate store
    
    if _memory_store is None:
        db = client[settings.database_name]
        _memory_store = MongoDBStore(
            collection=db["memory_store"],
        )
    
    return _memory_store
