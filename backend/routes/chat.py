"""
Chat endpoints with streaming support and rate limiting.
"""

import json
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from models.schemas import ChatRequest, ChatResponse, Message
from agent import invoke_chat, stream_chat
from config import DEFAULT_MODEL, get_settings
from database import get_database
from middleware.rate_limiter import limiter

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
@limiter.limit(lambda: f"{get_settings().rate_limit_per_hour}/hour")
async def chat(request: Request, chat_request: ChatRequest) -> ChatResponse:
    """
    Send a message and receive a response.
    
    Creates a new conversation if conversation_id is not provided.
    Rate limited to N requests/hour per user.
    """
    # Cache parsed body on request state for rate limiter key function
    request.state._parsed_body = chat_request.model_dump()
    
    # Generate conversation ID if not provided
    conversation_id = chat_request.conversation_id or str(uuid.uuid4())
    model_name = chat_request.model_name or DEFAULT_MODEL
    
    try:
        # Invoke the chat graph
        response, messages, tool_metadata, token_usage = invoke_chat(
            message=chat_request.message,
            user_id=chat_request.user_id,
            conversation_id=conversation_id,
            model_name=model_name,
            tool_mode=chat_request.tool_mode,
            use_rag=chat_request.use_rag,
        )
        
        # Save to conversations collection
        await _save_conversation(
            conversation_id=conversation_id,
            user_id=chat_request.user_id,
            user_message=chat_request.message,
            assistant_response=response,
            model_name=model_name,
            is_new=chat_request.conversation_id is None,
            tool_metadata=tool_metadata,
            token_usage=token_usage,
        )
        
        return ChatResponse(
            response=response,
            conversation_id=conversation_id,
            model_used=model_name,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
@limiter.limit(lambda: f"{get_settings().rate_limit_per_hour}/hour")
async def chat_stream(request: Request, chat_request: ChatRequest):
    """
    Send a message and receive a streaming response.
    
    Uses Server-Sent Events (SSE) for real-time streaming.
    Rate limited to N requests/hour per user.
    """
    # Cache parsed body on request state for rate limiter key function
    request.state._parsed_body = chat_request.model_dump()
    
    # Debug logging for request parameters
    print(f"[Chat Stream] Received request:")
    print(f"  - conversation_id: {chat_request.conversation_id}")
    print(f"  - tool_mode: {chat_request.tool_mode}")
    print(f"  - use_rag: {chat_request.use_rag}")
    print(f"  - user_id: {chat_request.user_id}")
    print(f"  - message: {chat_request.message[:50]}...")
    
    conversation_id = chat_request.conversation_id or str(uuid.uuid4())
    model_name = chat_request.model_name or DEFAULT_MODEL
    
    print(f"[Chat Stream] Using conversation_id: {conversation_id} (was new: {chat_request.conversation_id is None})")
    
    async def event_generator():
        """Generate SSE events from the stream."""
        full_response = ""
        tool_metadata = {}
        token_usage = {}
        
        try:
            async for chunk in stream_chat(
                message=chat_request.message,
                user_id=chat_request.user_id,
                conversation_id=conversation_id,
                model_name=model_name,
                tool_mode=chat_request.tool_mode,
                use_rag=chat_request.use_rag,
            ):
                # Check if this is metadata (tool_metadata + token_usage)
                if isinstance(chunk, dict) and "tool_metadata" in chunk:
                    tool_metadata = chunk["tool_metadata"]
                    token_usage = chunk.get("token_usage", {})
                    continue
                
                full_response += chunk
                yield {
                    "event": "message",
                    "data": chunk,
                }
            
            # Send completion event with metadata including token usage
            done_data = {
                "conversation_id": conversation_id,
                "model_used": model_name,
                "tool_metadata": tool_metadata,
                "token_usage": token_usage,
            }
            print(f"[Chat Stream] Sending done event with data: {done_data}")
            yield {
                "event": "done",
                "data": json.dumps(done_data),
            }
            
            # Save conversation after streaming completes
            await _save_conversation(
                conversation_id=conversation_id,
                user_id=chat_request.user_id,
                user_message=chat_request.message,
                assistant_response=full_response,
                model_name=model_name,
                is_new=chat_request.conversation_id is None,
                tool_metadata=tool_metadata,
                token_usage=token_usage,
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
    token_usage: dict | None = None,
) -> None:
    """Save or update conversation in MongoDB with token usage tracking."""
    print(f"[_save_conversation] Called with:")
    print(f"  - conversation_id: {conversation_id}")
    print(f"  - is_new: {is_new}")
    print(f"  - user_id: {user_id}")
    if token_usage:
        print(f"  - token_usage: {token_usage}")
    
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
        "token_usage": token_usage or {},
    }
    
    if is_new:
        print(f"[_save_conversation] Creating NEW conversation: {conversation_id}")
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
    title = message.split("\n")[0].strip()
    if len(title) > max_length:
        title = title[:max_length - 3] + "..."
    return title or "New Chat"
