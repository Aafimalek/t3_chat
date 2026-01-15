"""
Chat endpoints with streaming support.
"""

import json
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from models.schemas import ChatRequest, ChatResponse, Message
from agent import invoke_chat, stream_chat
from config import DEFAULT_MODEL
from database import get_database

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Send a message and receive a response.
    
    Creates a new conversation if conversation_id is not provided.
    """
    # Generate conversation ID if not provided
    conversation_id = request.conversation_id or str(uuid.uuid4())
    model_name = request.model_name or DEFAULT_MODEL
    
    try:
        # Invoke the chat graph
        response, messages, tool_metadata = invoke_chat(
            message=request.message,
            user_id=request.user_id,
            conversation_id=conversation_id,
            model_name=model_name,
            tool_mode=request.tool_mode,
            use_rag=request.use_rag,
        )
        
        # Save to conversations collection
        await _save_conversation(
            conversation_id=conversation_id,
            user_id=request.user_id,
            user_message=request.message,
            assistant_response=response,
            model_name=model_name,
            is_new=request.conversation_id is None,
            tool_metadata=tool_metadata,
        )
        
        return ChatResponse(
            response=response,
            conversation_id=conversation_id,
            model_used=model_name,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    Send a message and receive a streaming response.
    
    Uses Server-Sent Events (SSE) for real-time streaming.
    """
    # Debug logging for request parameters
    print(f"[Chat Stream] Received request:")
    print(f"  - conversation_id: {request.conversation_id}")
    print(f"  - tool_mode: {request.tool_mode}")
    print(f"  - use_rag: {request.use_rag}")
    print(f"  - user_id: {request.user_id}")
    print(f"  - message: {request.message[:50]}...")
    
    conversation_id = request.conversation_id or str(uuid.uuid4())
    model_name = request.model_name or DEFAULT_MODEL
    
    print(f"[Chat Stream] Using conversation_id: {conversation_id} (was new: {request.conversation_id is None})")
    
    async def event_generator():
        """Generate SSE events from the stream."""
        full_response = ""
        tool_metadata = {}
        
        try:
            async for chunk in stream_chat(
                message=request.message,
                user_id=request.user_id,
                conversation_id=conversation_id,
                model_name=model_name,
                tool_mode=request.tool_mode,
                use_rag=request.use_rag,
            ):
                # Check if this is tool metadata
                if isinstance(chunk, dict) and "tool_metadata" in chunk:
                    tool_metadata = chunk["tool_metadata"]
                    continue
                
                full_response += chunk
                yield {
                    "event": "message",
                    "data": chunk,
                }
            
            # Send completion event with metadata
            # Explicitly JSON encode to ensure proper SSE format
            done_data = {
                "conversation_id": conversation_id,
                "model_used": model_name,
                "tool_metadata": tool_metadata,
            }
            print(f"[Chat Stream] Sending done event with data: {done_data}")
            yield {
                "event": "done",
                "data": json.dumps(done_data),  # Explicitly JSON encode to ensure proper format
            }
            
            # Save conversation after streaming completes
            await _save_conversation(
                conversation_id=conversation_id,
                user_id=request.user_id,
                user_message=request.message,
                assistant_response=full_response,
                model_name=model_name,
                is_new=request.conversation_id is None,
                tool_metadata=tool_metadata,
            )
            
        except Exception as e:
            yield {
                "event": "error",
                "data": str(e),
            }
    
    return EventSourceResponse(event_generator())


async def _save_conversation(
    conversation_id: str,
    user_id: str,
    user_message: str,
    assistant_response: str,
    model_name: str,
    is_new: bool,
    tool_metadata: dict | None = None,
) -> None:
    """Save or update conversation in MongoDB."""
    print(f"[_save_conversation] Called with:")
    print(f"  - conversation_id: {conversation_id}")
    print(f"  - is_new: {is_new}")
    print(f"  - user_id: {user_id}")
    
    db = await get_database()
    conversations = db["conversations"]
    
    now = datetime.utcnow()
    
    user_msg = {
        "role": "user",
        "content": user_message,
        "timestamp": now,
    }
    
    assistant_msg = {
        "role": "assistant",
        "content": assistant_response,
        "timestamp": now,
        "tool_metadata": tool_metadata or {},
    }
    
    if is_new:
        print(f"[_save_conversation] Creating NEW conversation: {conversation_id}")
        # Create new conversation
        title = _generate_title(user_message)
        await conversations.insert_one({
            "_id": conversation_id,
            "user_id": user_id,
            "title": title,
            "model_name": model_name,
            "messages": [user_msg, assistant_msg],
            "created_at": now,
            "updated_at": now,
        })
    else:
        # Check if conversation exists, create if not (for RAG upload before first message)
        print(f"[_save_conversation] Checking if conversation {conversation_id} exists...")
        existing = await conversations.find_one({"_id": conversation_id})
        if not existing:
            print(f"[_save_conversation] Conversation NOT found, creating new: {conversation_id}")
            title = _generate_title(user_message)
            await conversations.insert_one({
                "_id": conversation_id,
                "user_id": user_id,
                "title": title,
                "model_name": model_name,
                "messages": [user_msg, assistant_msg],
                "created_at": now,
                "updated_at": now,
            })
        else:
            # Update existing conversation
            print(f"[_save_conversation] Conversation FOUND, updating: {conversation_id}")
            await conversations.update_one(
                {"_id": conversation_id},
                {
                    "$push": {
                        "messages": {"$each": [user_msg, assistant_msg]}
                    },
                    "$set": {"updated_at": now},
                }
            )
            print(f"[_save_conversation] Successfully updated conversation: {conversation_id}")


def _generate_title(message: str, max_length: int = 50) -> str:
    """Generate a title from the first message."""
    # Simple title generation - first line, truncated
    title = message.split("\n")[0].strip()
    if len(title) > max_length:
        title = title[:max_length - 3] + "..."
    return title or "New Chat"
