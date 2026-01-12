"""
MongoDB database connection and lifecycle management.
"""

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

from config import get_settings


# Global database instances
_async_client: AsyncIOMotorClient | None = None
_sync_client: MongoClient | None = None


async def get_async_client() -> AsyncIOMotorClient:
    """Get the async MongoDB client, creating it if necessary."""
    global _async_client
    if _async_client is None:
        settings = get_settings()
        _async_client = AsyncIOMotorClient(settings.mongodb_url)
    return _async_client


async def get_database():
    """Get the async database instance."""
    client = await get_async_client()
    settings = get_settings()
    return client[settings.database_name]


def get_sync_client() -> MongoClient:
    """Get the sync MongoDB client for LangGraph checkpointer."""
    global _sync_client
    if _sync_client is None:
        settings = get_settings()
        _sync_client = MongoClient(settings.mongodb_url)
    return _sync_client


def get_sync_database():
    """Get the sync database instance."""
    client = get_sync_client()
    settings = get_settings()
    return client[settings.database_name]


async def close_connections():
    """Close all database connections."""
    global _async_client, _sync_client
    
    if _async_client is not None:
        _async_client.close()
        _async_client = None
    
    if _sync_client is not None:
        _sync_client.close()
        _sync_client = None
