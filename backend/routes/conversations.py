"""
Conversation management endpoints.
"""

from fastapi import APIRouter, HTTPException, Query

from models.schemas import Conversation, ConversationSummary, ConversationUpdate
from database import get_database

router = APIRouter(prefix="/api/conversations", tags=["Conversations"])


@router.get("", response_model=list[ConversationSummary])
async def list_conversations(
    user_id: str = Query(..., description="User identifier"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[ConversationSummary]:
    """List all conversations for a user."""
    db = await get_database()
    conversations = db["conversations"]
    
    cursor = conversations.find(
        {"user_id": user_id}
    ).sort("updated_at", -1).skip(offset).limit(limit)
    
    results = []
    async for doc in cursor:
        results.append(ConversationSummary(
            id=doc["_id"],
            title=doc["title"],
            model_name=doc["model_name"],
            created_at=doc["created_at"],
            updated_at=doc["updated_at"],
            message_count=len(doc.get("messages", [])),
        ))
    
    return results


@router.get("/{conversation_id}", response_model=Conversation)
async def get_conversation(
    conversation_id: str,
    user_id: str = Query(..., description="User identifier"),
) -> Conversation:
    """Get a specific conversation with all messages."""
    db = await get_database()
    conversations = db["conversations"]
    
    doc = await conversations.find_one({
        "_id": conversation_id,
        "user_id": user_id,
    })
    
    if not doc:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )
    
    return Conversation(
        id=doc["_id"],
        user_id=doc["user_id"],
        title=doc["title"],
        model_name=doc["model_name"],
        messages=doc.get("messages", []),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


@router.patch("/{conversation_id}", response_model=Conversation)
async def update_conversation(
    conversation_id: str,
    update: ConversationUpdate,
    user_id: str = Query(..., description="User identifier"),
) -> Conversation:
    """Update a conversation (e.g., rename)."""
    db = await get_database()
    conversations = db["conversations"]
    
    # Build update document
    update_doc = {}
    if update.title is not None:
        update_doc["title"] = update.title
    
    if not update_doc:
        raise HTTPException(
            status_code=400,
            detail="No valid fields to update"
        )
    
    result = await conversations.find_one_and_update(
        {"_id": conversation_id, "user_id": user_id},
        {"$set": update_doc},
        return_document=True,
    )
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )
    
    return Conversation(
        id=result["_id"],
        user_id=result["user_id"],
        title=result["title"],
        model_name=result["model_name"],
        messages=result.get("messages", []),
        created_at=result["created_at"],
        updated_at=result["updated_at"],
    )


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user_id: str = Query(..., description="User identifier"),
) -> dict:
    """Delete a conversation."""
    db = await get_database()
    conversations = db["conversations"]
    
    result = await conversations.delete_one({
        "_id": conversation_id,
        "user_id": user_id,
    })
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )
    
    return {"message": "Conversation deleted", "id": conversation_id}
