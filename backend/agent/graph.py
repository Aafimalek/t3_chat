"""
LangGraph workflow for chat processing with memory integration.
"""

from typing import Annotated, AsyncIterator
from typing_extensions import TypedDict

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from agent.llm_provider import get_llm
from agent.prompts import SYSTEM_PROMPT
from memory.checkpointer import get_checkpointer
from memory.manager import MemoryManager


# ============================================================================
# State Definition
# ============================================================================

class ChatState(TypedDict):
    """State for the chat graph."""
    messages: Annotated[list, add_messages]
    user_id: str
    model_name: str
    memory_context: str


# ============================================================================
# Graph Nodes
# ============================================================================

def load_memory(state: ChatState) -> dict:
    """Load relevant memories for the current conversation."""
    user_id = state["user_id"]
    messages = state["messages"]
    
    # Get the latest user message for memory search
    last_user_msg = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_user_msg = msg.content
            break
    
    # Search for relevant memories
    memory_manager = MemoryManager(user_id)
    memory_context = memory_manager.get_context_memories(
        query=last_user_msg,
        limit=5
    )
    
    return {"memory_context": memory_context}


def generate_response(state: ChatState) -> dict:
    """Generate a response using the LLM."""
    model_name = state["model_name"]
    memory_context = state.get("memory_context", "")
    
    # Build system message with memory context
    system_content = SYSTEM_PROMPT.format(
        memory_context=memory_context if memory_context else ""
    )
    
    # Get the LLM
    llm = get_llm(model_name=model_name, streaming=False)
    
    # Prepare messages with system prompt
    messages = [SystemMessage(content=system_content)] + state["messages"]
    
    # Generate response
    response = llm.invoke(messages)
    
    return {"messages": [response]}


async def generate_response_stream(state: ChatState) -> AsyncIterator[str]:
    """Generate a streaming response using the LLM."""
    model_name = state["model_name"]
    memory_context = state.get("memory_context", "")
    
    # Build system message with memory context
    system_content = SYSTEM_PROMPT.format(
        memory_context=memory_context if memory_context else ""
    )
    
    # Get the LLM with streaming enabled
    llm = get_llm(model_name=model_name, streaming=True)
    
    # Prepare messages with system prompt
    messages = [SystemMessage(content=system_content)] + state["messages"]
    
    # Stream the response
    async for chunk in llm.astream(messages):
        if chunk.content:
            yield chunk.content


# ============================================================================
# Graph Construction
# ============================================================================

def create_chat_graph() -> StateGraph:
    """Create the chat processing graph."""
    # Build the graph
    builder = StateGraph(ChatState)
    
    # Add nodes
    builder.add_node("load_memory", load_memory)
    builder.add_node("generate_response", generate_response)
    
    # Add edges
    builder.add_edge(START, "load_memory")
    builder.add_edge("load_memory", "generate_response")
    builder.add_edge("generate_response", END)
    
    # Compile with checkpointer for persistence
    checkpointer = get_checkpointer()
    return builder.compile(checkpointer=checkpointer)


# ============================================================================
# Convenience Functions
# ============================================================================

def invoke_chat(
    message: str,
    user_id: str,
    conversation_id: str,
    model_name: str | None = None,
) -> tuple[str, list]:
    """
    Invoke the chat graph with a message.
    
    Args:
        message: The user's message
        user_id: User identifier
        conversation_id: Thread ID for conversation persistence
        model_name: Optional model to use
        
    Returns:
        Tuple of (response_text, all_messages)
    """
    from config import DEFAULT_MODEL
    
    graph = create_chat_graph()
    
    config = {"configurable": {"thread_id": conversation_id}}
    
    result = graph.invoke(
        {
            "messages": [HumanMessage(content=message)],
            "user_id": user_id,
            "model_name": model_name or DEFAULT_MODEL,
            "memory_context": "",
        },
        config=config,
    )
    
    # Extract the response
    messages = result["messages"]
    response = messages[-1].content if messages else ""
    
    return response, messages


async def stream_chat(
    message: str,
    user_id: str,
    conversation_id: str,
    model_name: str | None = None,
) -> AsyncIterator[str]:
    """
    Stream a chat response.
    
    Args:
        message: The user's message
        user_id: User identifier
        conversation_id: Thread ID for conversation persistence
        model_name: Optional model to use
        
    Yields:
        Response chunks as they're generated
    """
    from config import DEFAULT_MODEL
    
    # First, load memories
    memory_manager = MemoryManager(user_id)
    memory_context = memory_manager.get_context_memories(query=message, limit=5)
    
    # Create state
    state = ChatState(
        messages=[HumanMessage(content=message)],
        user_id=user_id,
        model_name=model_name or DEFAULT_MODEL,
        memory_context=memory_context,
    )
    
    # Stream the response
    full_response = ""
    async for chunk in generate_response_stream(state):
        full_response += chunk
        yield chunk
    
    # After streaming, save to graph for persistence
    graph = create_chat_graph()
    config = {"configurable": {"thread_id": conversation_id}}
    
    # Update the graph state with the full conversation
    graph.invoke(
        {
            "messages": [
                HumanMessage(content=message),
                AIMessage(content=full_response),
            ],
            "user_id": user_id,
            "model_name": model_name or DEFAULT_MODEL,
            "memory_context": memory_context,
        },
        config=config,
    )
