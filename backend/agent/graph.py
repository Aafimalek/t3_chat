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
from utils.context_manager import manage_context


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
    token_usage: dict


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

=== CRITICAL: TOOL RESULTS PROVIDED - YOU MUST USE THEM ===

You have been given REAL-TIME search results and/or document content below.
Your response MUST follow these rules:

1. **USE THE DATA**: Extract specific facts, dates, names, and details from the results.
2. **CITE SOURCES**: When stating facts from search results, include the source URL.
   Format: "According to [Source Name](URL), ..."
3. **BE SPECIFIC**: Include exact dates, times, locations, and details found in the results.
4. **NO GENERIC RESPONSES**: Do NOT say things like "check the official website" or 
   "I don't have current information" - THE RESULTS BELOW ARE CURRENT.
5. **ACKNOWLEDGE LIMITATIONS**: If the results don't contain the answer, say exactly what 
   information IS available and what is missing.

FORBIDDEN RESPONSES:
- "I recommend checking [website] for the latest information"
- "I don't have access to real-time data"
- "As of my knowledge cutoff..."
- Generic advice without specific facts from the results

REQUIRED FORMAT:
- Lead with the direct answer using facts from the results
- Cite at least one source URL
- Add relevant context from other results if available

"""
        system_content += tool_instructions + tool_context
    
    # Get the LLM
    llm = get_llm(model_name=model_name, streaming=False)
    
    # Apply context window management — trim/summarize if messages exceed budget
    trimmed_messages = manage_context(
        messages=state["messages"],
        model_name=model_name,
        system_prompt=system_content,
    )
    
    # Prepare messages with system prompt
    messages = [SystemMessage(content=system_content)] + trimmed_messages
    
    # Generate response
    response = llm.invoke(messages)
    
    # Extract token usage from Groq response metadata
    token_usage = {}
    if hasattr(response, "response_metadata") and response.response_metadata:
        usage = response.response_metadata.get("token_usage", {})
        if usage:
            token_usage = {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            }
    # Also check usage_metadata (newer langchain-core versions)
    if not token_usage and hasattr(response, "usage_metadata") and response.usage_metadata:
        um = response.usage_metadata
        if hasattr(um, "input_tokens") and um.input_tokens:
            token_usage = {
                "prompt_tokens": um.input_tokens,
                "completion_tokens": um.output_tokens or 0,
                "total_tokens": (um.input_tokens or 0) + (um.output_tokens or 0),
            }
    # Fallback: count with tiktoken if provider didn't supply usage
    if not token_usage or not token_usage.get("total_tokens"):
        from utils.token_counter import count_tokens, count_messages_tokens
        prompt_tokens = count_messages_tokens(messages)
        completion_tokens = count_tokens(response.content)
        token_usage = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        }
        print(f"[TokenUsage] Fallback tiktoken count: {token_usage}", flush=True)
    else:
        print(f"[TokenUsage] From provider metadata: {token_usage}", flush=True)
    
    return {
        "messages": [response],
        "last_assistant_response": response.content,
        "token_usage": token_usage,
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


async def generate_response_stream(state: ChatState) -> AsyncIterator[str | dict]:
    """Generate a streaming response using the LLM.
    
    Yields string chunks during generation, then a final dict with token_usage.
    """
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

=== CRITICAL: TOOL RESULTS PROVIDED - YOU MUST USE THEM ===

You have been given REAL-TIME search results and/or document content below.
Your response MUST follow these rules:

1. **USE THE DATA**: Extract specific facts, dates, names, and details from the results.
2. **CITE SOURCES**: When stating facts from search results, include the source URL.
   Format: "According to [Source Name](URL), ..."
3. **BE SPECIFIC**: Include exact dates, times, locations, and details found in the results.
4. **NO GENERIC RESPONSES**: Do NOT say things like "check the official website" or 
   "I don't have current information" - THE RESULTS BELOW ARE CURRENT.
5. **ACKNOWLEDGE LIMITATIONS**: If the results don't contain the answer, say exactly what 
   information IS available and what is missing.

FORBIDDEN RESPONSES:
- "I recommend checking [website] for the latest information"
- "I don't have access to real-time data"
- "As of my knowledge cutoff..."
- Generic advice without specific facts from the results

REQUIRED FORMAT:
- Lead with the direct answer using facts from the results
- Cite at least one source URL
- Add relevant context from other results if available

"""
        system_content += tool_instructions + tool_context
    
    # Get the LLM with streaming enabled
    llm = get_llm(model_name=model_name, streaming=True)
    
    # Apply context window management
    trimmed_messages = manage_context(
        messages=state["messages"],
        model_name=model_name,
        system_prompt=system_content,
    )
    
    # Prepare messages with system prompt
    messages = [SystemMessage(content=system_content)] + trimmed_messages
    
    # Stream the response and capture token usage from last chunk
    token_usage = {}
    full_response_text = ""
    async for chunk in llm.astream(messages):
        # Try to extract token usage from chunk metadata (Groq sends on last chunk)
        if hasattr(chunk, "response_metadata") and chunk.response_metadata:
            usage = chunk.response_metadata.get("token_usage", {})
            if usage:
                token_usage = {
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                }
        # Also check usage_metadata (newer langchain-core versions)
        if not token_usage and hasattr(chunk, "usage_metadata") and chunk.usage_metadata:
            um = chunk.usage_metadata
            if hasattr(um, "input_tokens") and um.input_tokens:
                token_usage = {
                    "prompt_tokens": um.input_tokens,
                    "completion_tokens": um.output_tokens or 0,
                    "total_tokens": (um.input_tokens or 0) + (um.output_tokens or 0),
                }
        if chunk.content:
            full_response_text += chunk.content
            yield chunk.content
    
    # Fallback: if provider didn't supply token usage, count with tiktoken
    if not token_usage or not token_usage.get("total_tokens"):
        from utils.token_counter import count_tokens, count_messages_tokens
        prompt_tokens = count_messages_tokens(messages)
        completion_tokens = count_tokens(full_response_text)
        token_usage = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        }
        print(f"[TokenUsage] Fallback tiktoken count: {token_usage}", flush=True)
    else:
        print(f"[TokenUsage] From provider metadata: {token_usage}", flush=True)
    
    # Yield token usage as a dict at the end of stream
    yield {"token_usage": token_usage}


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
) -> tuple[str, list, dict, dict]:
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
        Tuple of (response_text, all_messages, tool_metadata, token_usage)
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
            "token_usage": {},
        },
        config=config,
    )
    
    # Extract the response
    messages = result["messages"]
    response = messages[-1].content if messages else ""
    tool_metadata = result.get("tool_metadata", {})
    token_usage = result.get("token_usage", {})
    
    return response, messages, tool_metadata, token_usage


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
        Response chunks as they're generated, then metadata dicts
    """
    from config import DEFAULT_MODEL
    from agent.tools import get_tool_context
    
    # Debug logging
    print(f"[stream_chat] Called with:")
    print(f"  - message: {message[:50]}...")
    print(f"  - conversation_id: {conversation_id}")
    print(f"  - tool_mode: {tool_mode}")
    print(f"  - use_rag: {use_rag}")
    
    # Load conversation history from checkpointer for multi-turn context
    graph = create_chat_graph()
    config = {"configurable": {"thread_id": conversation_id}}
    
    prior_messages = []
    try:
        checkpoint_state = graph.get_state(config)
        if checkpoint_state and checkpoint_state.values:
            prior_messages = checkpoint_state.values.get("messages", [])
            print(f"[stream_chat] Loaded {len(prior_messages)} prior messages from checkpointer", flush=True)
    except Exception as e:
        print(f"[stream_chat] Could not load prior messages: {e}", flush=True)
    
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
    
    # Build message list: prior conversation + new user message
    all_messages = prior_messages + [HumanMessage(content=message)]
    
    # Create state
    state = ChatState(
        messages=all_messages,
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
        token_usage={},
    )
    
    # Stream the response
    full_response = ""
    token_usage = {}
    async for chunk in generate_response_stream(state):
        # Check if this is the token_usage dict from the end of stream
        if isinstance(chunk, dict) and "token_usage" in chunk:
            token_usage = chunk["token_usage"]
            continue
        full_response += chunk
        yield chunk
    
    # Yield tool metadata and token usage at the end
    yield {"tool_metadata": tool_metadata, "token_usage": token_usage}
    
    # After streaming, save to graph for persistence and extract memories
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
            "token_usage": {},
        },
        config=config,
    )
