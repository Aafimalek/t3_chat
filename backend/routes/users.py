"""
User and memory management endpoints.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from memory.manager import MemoryManager
from database import get_database

router = APIRouter(prefix="/api/users", tags=["Users"])


class UserProfile(BaseModel):
    """User profile data."""
    id: str
    email: str | None = None
    name: str | None = None
    image_url: str | None = None


class AboutYou(BaseModel):
    """User's 'About You' settings - like ChatGPT."""
    nickname: str = ""
    occupation: str = ""
    about: str = ""
    memory_enabled: bool = True


class MemoryItem(BaseModel):
    """A single memory item."""
    key: str
    type: str
    content: str
    created_at: str


class SaveFactRequest(BaseModel):
    """Request to save a fact."""
    fact: str


# ============================================================================
# Profile Endpoints
# ============================================================================

@router.get("/{user_id}/profile", response_model=UserProfile)
async def get_user_profile(user_id: str) -> UserProfile:
    """Get or create a user profile."""
    db = await get_database()
    users = db["users"]
    
    user = await users.find_one({"_id": user_id})
    
    if not user:
        # Create a basic profile
        user = {
            "_id": user_id,
            "email": None,
            "name": None,
            "image_url": None,
        }
        await users.insert_one(user)
    
    return UserProfile(
        id=user["_id"],
        email=user.get("email"),
        name=user.get("name"),
        image_url=user.get("image_url"),
    )


@router.put("/{user_id}/profile", response_model=UserProfile)
async def update_user_profile(user_id: str, profile: UserProfile) -> UserProfile:
    """Update user profile from Clerk data."""
    db = await get_database()
    users = db["users"]
    
    await users.update_one(
        {"_id": user_id},
        {
            "$set": {
                "email": profile.email,
                "name": profile.name,
                "image_url": profile.image_url,
            }
        },
        upsert=True,
    )
    
    return profile


# ============================================================================
# About You Endpoints (ChatGPT-style)
# ============================================================================

@router.get("/{user_id}/about", response_model=AboutYou)
async def get_about_you(user_id: str) -> AboutYou:
    """Get user's About You settings."""
    db = await get_database()
    settings = db["user_settings"]
    
    doc = await settings.find_one({"_id": user_id})
    
    if not doc:
        return AboutYou()
    
    return AboutYou(
        nickname=doc.get("nickname", ""),
        occupation=doc.get("occupation", ""),
        about=doc.get("about", ""),
        memory_enabled=doc.get("memory_enabled", True),
    )


@router.put("/{user_id}/about", response_model=AboutYou)
async def update_about_you(user_id: str, about: AboutYou) -> AboutYou:
    """Update user's About You settings and sync to memories."""
    db = await get_database()
    settings = db["user_settings"]
    
    # Save settings
    await settings.update_one(
        {"_id": user_id},
        {
            "$set": {
                "nickname": about.nickname,
                "occupation": about.occupation,
                "about": about.about,
                "memory_enabled": about.memory_enabled,
            }
        },
        upsert=True,
    )
    
    # Also save core facts to memory for the LLM to use
    memory_manager = MemoryManager(user_id)
    now = datetime.utcnow().isoformat()
    
    # Save nickname as a core memory
    if about.nickname:
        memory_manager.save_memory(
            key="core_nickname",
            value={
                "type": "core_fact",
                "content": f"User's name/nickname is {about.nickname}",
                "source": "settings",
                "created_at": now,
            }
        )
    
    # Save occupation
    if about.occupation:
        memory_manager.save_memory(
            key="core_occupation",
            value={
                "type": "core_fact",
                "content": f"User works as/is a {about.occupation}",
                "source": "settings",
                "created_at": now,
            }
        )
    
    # Save about text
    if about.about:
        memory_manager.save_memory(
            key="core_about",
            value={
                "type": "core_fact",
                "content": f"About user: {about.about}",
                "source": "settings",
                "created_at": now,
            }
        )
    
    return about


# ============================================================================
# Memory Endpoints
# ============================================================================

@router.get("/{user_id}/memories", response_model=list[MemoryItem])
async def get_user_memories(
    user_id: str,
    limit: int = Query(50, ge=1, le=100),
) -> list[MemoryItem]:
    """Get all memories for a user."""
    memory_manager = MemoryManager(user_id)
    memories = memory_manager.list_memories(limit=limit)
    
    result = []
    for item in memories:
        value = item.value if hasattr(item, 'value') else item.get('value', {})
        key = item.key if hasattr(item, 'key') else item.get('key', '')
        
        if isinstance(value, dict):
            result.append(MemoryItem(
                key=key,
                type=value.get("type", "unknown"),
                content=value.get("content", value.get("value", "")),
                created_at=value.get("created_at", value.get("updated_at", "")),
            ))
    
    return result


@router.post("/{user_id}/memories")
async def save_user_memory(user_id: str, request: SaveFactRequest) -> dict:
    """Manually save a fact for a user."""
    memory_manager = MemoryManager(user_id)
    key = memory_manager.save_fact(request.fact, source="manual")
    
    if key:
        return {"message": "Fact saved", "key": key}
    return {"message": "Fact already exists", "key": None}


@router.delete("/{user_id}/memories/{memory_key}")
async def delete_user_memory(user_id: str, memory_key: str) -> dict:
    """Delete a specific memory."""
    memory_manager = MemoryManager(user_id)
    memory_manager.delete_memory(memory_key)
    return {"message": "Memory deleted", "key": memory_key}


@router.delete("/{user_id}/memories")
async def clear_user_memories(user_id: str) -> dict:
    """Clear all memories for a user."""
    memory_manager = MemoryManager(user_id)
    count = memory_manager.clear_all_memories()
    return {"message": f"Cleared {count} memories"}
