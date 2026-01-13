"""
Memory cleanup utilities.

Handles deletion of short-term memory (checkpoints, checkpoint_writes)
when conversations are deleted, while preserving long-term memories.
"""

from database import get_sync_database
from config import get_settings


def delete_checkpoints(conversation_id: str) -> int:
    """
    Delete all checkpoints for a conversation.
    
    Checkpoints store the LangGraph state snapshots for conversation continuity.
    These should be deleted when a conversation is removed.
    
    Args:
        conversation_id: The conversation/thread ID
        
    Returns:
        Number of checkpoints deleted
    """
    db = get_sync_database()
    checkpoints_collection = db["checkpoints"]
    
    # Delete all checkpoints for this thread_id
    result = checkpoints_collection.delete_many({
        "thread_id": conversation_id
    })
    
    return result.deleted_count


def delete_checkpoint_writes(conversation_id: str) -> int:
    """
    Delete all checkpoint writes for a conversation.
    
    Checkpoint writes store individual graph operations.
    These should be deleted when a conversation is removed.
    
    Args:
        conversation_id: The conversation/thread ID
        
    Returns:
        Number of checkpoint writes deleted
    """
    db = get_sync_database()
    checkpoint_writes_collection = db["checkpoint_writes"]
    
    # Delete all checkpoint writes for this thread_id
    result = checkpoint_writes_collection.delete_many({
        "thread_id": conversation_id
    })
    
    return result.deleted_count


def cleanup_conversation_memory(conversation_id: str) -> dict:
    """
    Clean up all short-term memory associated with a conversation.
    
    This function deletes:
    - Checkpoints (graph state snapshots)
    - Checkpoint writes (graph operations)
    
    Long-term memories in the memory_store are NOT deleted and will
    persist for use in future conversations.
    
    Args:
        conversation_id: The conversation/thread ID to clean up
        
    Returns:
        Dictionary with cleanup statistics
    """
    checkpoints_deleted = delete_checkpoints(conversation_id)
    checkpoint_writes_deleted = delete_checkpoint_writes(conversation_id)
    
    return {
        "conversation_id": conversation_id,
        "checkpoints_deleted": checkpoints_deleted,
        "checkpoint_writes_deleted": checkpoint_writes_deleted,
        "long_term_memories": "preserved",
    }


def cleanup_user_short_term_memory(user_id: str) -> dict:
    """
    Clean up ALL short-term memory for a user across all conversations.
    
    This is a more aggressive cleanup that removes all checkpoints and
    checkpoint writes for a user. Long-term memories are still preserved.
    
    Args:
        user_id: The user ID
        
    Returns:
        Dictionary with cleanup statistics
    """
    db = get_sync_database()
    
    # We need to find all conversation IDs for this user first
    conversations = db["conversations"]
    user_conversations = conversations.find({"user_id": user_id}, {"_id": 1})
    
    total_checkpoints = 0
    total_writes = 0
    
    for conv in user_conversations:
        conv_id = conv["_id"]
        checkpoints_deleted = delete_checkpoints(conv_id)
        writes_deleted = delete_checkpoint_writes(conv_id)
        
        total_checkpoints += checkpoints_deleted
        total_writes += writes_deleted
    
    return {
        "user_id": user_id,
        "total_checkpoints_deleted": total_checkpoints,
        "total_checkpoint_writes_deleted": total_writes,
        "long_term_memories": "preserved",
    }
