"""
LangGraph workflow for chat processing with memory integration.
"""

from typing import Annotated, AsyncIterator
from typing_extensions import TypedDict

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from agent.llm_provider import get_llm
from agent.prompts import SYSTEM_PROMPT, MEMORY_EXTRACTION_PROMPT
from memory.checkpointer import get_checkpointer
from memory.manager import MemoryManager, extract_facts_from_response


# ============================================================================
# State Definition
# ============================================================================

class ChatState(TypedDict):
    """State for the chat graph."""
    messages: Annotated[list, add_messages]
    user_id: str
    model_name: str
    memory_context: str
    last_user_message: str
    last_assistant_response: str
    tool_context: str
    tool_mode: str
    use_rag: bool
    conversation_id: str
    tool_metadata: dict


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
        limit=10
    )
    
    return {
        "memory_context": memory_context,
        "last_user_message": last_user_msg,
    }


def load_tool_context(state: ChatState) -> dict:
    """Load tool context (search and/or RAG) for the query."""
    from agent.tools import get_tool_context
    
    last_user_msg = state.get("last_user_message", "")
    conversation_id = state.get("conversation_id", "")
    tool_mode = state.get("tool_mode", "auto")
    use_rag = state.get("use_rag", True)
    
    if not last_user_msg:
        return {"tool_context": "", "tool_metadata": {}}
    
    tool_context, tool_metadata = get_tool_context(
        query=last_user_msg,
        conversation_id=conversation_id,
        tool_mode=tool_mode,
        use_rag=use_rag,
    )
    
    return {
        "tool_context": tool_context,
        "tool_metadata": tool_metadata,
    }


def generate_response(state: ChatState) -> dict:
    """Generate a response using the LLM."""
    model_name = state["model_name"]
    memory_context = state.get("memory_context", "")
    tool_context = state.get("tool_context", "")
    tool_metadata = state.get("tool_metadata", {})
    
    # Build system message with memory and tool context
    system_content = SYSTEM_PROMPT.format(
        memory_context=memory_context if memory_context else ""
    )
    
    # Add tool context if available
    if tool_context:
        tool_instructions = """

IMPORTANT: You have been provided with tool results (search and/or document retrieval).
- Use the information provided to give a specific, grounded answer
- Cite sources when using search results
- If the tool results don't contain relevant information, acknowledge this and provide the best answer you can
- Do NOT give generic responses - always reference the specific data provided"""
        system_content += tool_instructions + tool_context
    
    # Get the LLM
    llm = get_llm(model_name=model_name, streaming=False)
    
    # Prepare messages with system prompt
    messages = [SystemMessage(content=system_content)] + state["messages"]
    
    # Generate response
    response = llm.invoke(messages)
    
    return {
        "messages": [response],
        "last_assistant_response": response.content,
    }


def extract_memories(state: ChatState) -> dict:
    """Extract facts from the conversation and save to long-term memory."""
    user_id = state["user_id"]
    user_message = state.get("last_user_message", "")
    assistant_response = state.get("last_assistant_response", "")
    
    # Skip extraction if no meaningful user message
    if not user_message or len(user_message) < 10:
        return {}
    
    # Skip for very short exchanges
    if len(user_message) + len(assistant_response) < 50:
        return {}
    
    try:
        # Use a fast model for extraction
        llm = get_llm(model_name="llama-3.1-8b-instant", streaming=False)
        
        # Create extraction prompt
        extraction_prompt = MEMORY_EXTRACTION_PROMPT.format(
            user_message=user_message,
            assistant_response=assistant_response,
        )
        
        # Get extraction
        result = llm.invoke([HumanMessage(content=extraction_prompt)])
        
        # Parse and save facts
        facts = extract_facts_from_response(result.content)
        
        if facts:
            memory_manager = MemoryManager(user_id)
            memory_manager.save_facts_batch(facts, source="conversation")
    except Exception:
        # Don't fail the main flow if extraction fails
        pass
    
    return {}


async def generate_response_stream(state: ChatState) -> AsyncIterator[str]:
    """Generate a streaming response using the LLM."""
    model_name = state["model_name"]
    memory_context = state.get("memory_context", "")
    tool_context = state.get("tool_context", "")
    
    # Build system message with memory and tool context
    system_content = SYSTEM_PROMPT.format(
        memory_context=memory_context if memory_context else ""
    )
    
    # Add tool context if available
    if tool_context:
        tool_instructions = """

IMPORTANT: You have been provided with tool results (search and/or document retrieval).
- Use the information provided to give a specific, grounded answer
- Cite sources when using search results
- If the tool results don't contain relevant information, acknowledge this and provide the best answer you can
- Do NOT give generic responses - always reference the specific data provided"""
        system_content += tool_instructions + tool_context
    
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
    builder.add_node("load_tool_context", load_tool_context)
    builder.add_node("generate_response", generate_response)
    builder.add_node("extract_memories", extract_memories)
    
    # Add edges: load_memory -> load_tools -> generate -> extract -> end
    builder.add_edge(START, "load_memory")
    builder.add_edge("load_memory", "load_tool_context")
    builder.add_edge("load_tool_context", "generate_response")
    builder.add_edge("generate_response", "extract_memories")
    builder.add_edge("extract_memories", END)
    
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
    tool_mode: str = "auto",
    use_rag: bool = True,
) -> tuple[str, list, dict]:
    """
    Invoke the chat graph with a message.
    
    Args:
        message: The user's message
        user_id: User identifier
        conversation_id: Thread ID for conversation persistence
        model_name: Optional model to use
        tool_mode: Tool mode setting (auto/search/none)
        use_rag: Whether to use RAG
        
    Returns:
        Tuple of (response_text, all_messages, tool_metadata)
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
            "last_user_message": "",
            "last_assistant_response": "",
            "tool_context": "",
            "tool_mode": tool_mode,
            "use_rag": use_rag,
            "conversation_id": conversation_id,
            "tool_metadata": {},
        },
        config=config,
    )
    
    # Extract the response
    messages = result["messages"]
    response = messages[-1].content if messages else ""
    tool_metadata = result.get("tool_metadata", {})
    
    return response, messages, tool_metadata


async def stream_chat(
    message: str,
    user_id: str,
    conversation_id: str,
    model_name: str | None = None,
    tool_mode: str = "auto",
    use_rag: bool = True,
) -> AsyncIterator[str | dict]:
    """
    Stream a chat response.
    
    Args:
        message: The user's message
        user_id: User identifier
        conversation_id: Thread ID for conversation persistence
        model_name: Optional model to use
        tool_mode: Tool mode setting (auto/search/none)
        use_rag: Whether to use RAG
        
    Yields:
        Response chunks as they're generated, then tool metadata dict
    """
    from config import DEFAULT_MODEL
    from agent.tools import get_tool_context
    
    # Debug logging
    print(f"[stream_chat] Called with:")
    print(f"  - message: {message[:50]}...")
    print(f"  - conversation_id: {conversation_id}")
    print(f"  - tool_mode: {tool_mode}")
    print(f"  - use_rag: {use_rag}")
    
    # First, load memories
    memory_manager = MemoryManager(user_id)
    memory_context = memory_manager.get_context_memories(query=message, limit=10)
    
    # Load tool context (search and/or RAG)
    print(f"[stream_chat] Calling get_tool_context with tool_mode={tool_mode}")
    tool_context, tool_metadata = get_tool_context(
        query=message,
        conversation_id=conversation_id,
        tool_mode=tool_mode,
        use_rag=use_rag,
    )
    print(f"[stream_chat] Got tool_context length: {len(tool_context)}, metadata: {tool_metadata}")
    
    # Create state
    state = ChatState(
        messages=[HumanMessage(content=message)],
        user_id=user_id,
        model_name=model_name or DEFAULT_MODEL,
        memory_context=memory_context,
        last_user_message=message,
        last_assistant_response="",
        tool_context=tool_context,
        tool_mode=tool_mode,
        use_rag=use_rag,
        conversation_id=conversation_id,
        tool_metadata=tool_metadata,
    )
    
    # Stream the response
    full_response = ""
    async for chunk in generate_response_stream(state):
        full_response += chunk
        yield chunk
    
    # Yield tool metadata at the end
    yield {"tool_metadata": tool_metadata}
    
    # After streaming, save to graph for persistence and extract memories
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
            "last_user_message": message,
            "last_assistant_response": full_response,
            "tool_context": tool_context,
            "tool_mode": tool_mode,
            "use_rag": use_rag,
            "conversation_id": conversation_id,
            "tool_metadata": tool_metadata,
        },
        config=config,
    )
