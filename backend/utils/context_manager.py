"""
Smart Context Window Manager.

Implements a sliding window + summarization strategy:
1. Always keep the system message and latest user message.
2. Walk backwards through conversation history, fitting as many
   recent messages as possible within the token budget.
3. If older messages are dropped, summarize them into a compact
   "conversation summary" message inserted after the system prompt.
"""

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage

from utils.token_counter import count_tokens, count_messages_tokens, get_context_budget


def manage_context(
    messages: list[BaseMessage],
    model_name: str,
    system_prompt: str,
) -> list[BaseMessage]:
    """
    Trim and optionally summarize messages to fit within the model's context window.
    
    Args:
        messages: Full list of messages (excluding system prompt).
        model_name: The model being used (to look up context length).
        system_prompt: The system prompt text (already built with memory + tools).
    
    Returns:
        A list of messages that fit within the token budget, potentially
        with a summary of older messages prepended.
    """
    budget = get_context_budget(model_name)
    
    # Reserve tokens for the system prompt
    system_tokens = count_tokens(system_prompt) + 4  # +4 for message overhead
    remaining_budget = budget - system_tokens
    
    if remaining_budget <= 0:
        # System prompt alone exceeds budget — just return the last message
        print(f"[ContextManager] WARNING: System prompt ({system_tokens} tokens) exceeds budget ({budget})", flush=True)
        return messages[-1:] if messages else []
    
    # If all messages fit, return as-is (fast path)
    total_msg_tokens = count_messages_tokens(messages)
    if total_msg_tokens <= remaining_budget:
        return messages
    
    print(f"[ContextManager] Messages ({total_msg_tokens} tokens) exceed budget ({remaining_budget} tokens). Trimming...", flush=True)
    
    # Walk backwards, keeping recent messages that fit
    kept_messages: list[BaseMessage] = []
    kept_tokens = 0
    
    # Reserve ~500 tokens for the summary message if we need to truncate
    summary_reserve = 500
    effective_budget = remaining_budget - summary_reserve
    
    for msg in reversed(messages):
        msg_tokens = count_tokens(msg.content) + 4
        if kept_tokens + msg_tokens <= effective_budget:
            kept_messages.insert(0, msg)
            kept_tokens += msg_tokens
        else:
            break
    
    # If we kept everything (unlikely given the check above), return
    if len(kept_messages) == len(messages):
        return messages
    
    # Determine which messages were dropped
    dropped_count = len(messages) - len(kept_messages)
    dropped_messages = messages[:dropped_count]
    
    print(f"[ContextManager] Kept {len(kept_messages)} recent messages, summarizing {dropped_count} older messages", flush=True)
    
    # Generate a summary of dropped messages
    summary = _summarize_dropped_messages(dropped_messages)
    
    if summary:
        summary_msg = SystemMessage(
            content=f"[Summary of earlier conversation ({dropped_count} messages)]: {summary}"
        )
        return [summary_msg] + kept_messages
    
    return kept_messages


def _summarize_dropped_messages(messages: list[BaseMessage]) -> str:
    """
    Generate a concise summary of dropped messages.
    
    Uses a fast/cheap model (llama-3.1-8b-instant) for summarization.
    Falls back to a simple extraction if LLM call fails.
    """
    if not messages:
        return ""
    
    # Build a text representation of the dropped messages
    conversation_text = ""
    for msg in messages:
        role = "User" if isinstance(msg, HumanMessage) else "Assistant"
        # Truncate very long messages for the summary input
        content = msg.content[:500] if len(msg.content) > 500 else msg.content
        conversation_text += f"{role}: {content}\n"
    
    # Cap the input to prevent the summarizer itself from hitting limits
    if len(conversation_text) > 3000:
        conversation_text = conversation_text[:3000] + "\n[... truncated]"
    
    try:
        from agent.llm_provider import get_llm
        
        llm = get_llm(model_name="llama-3.1-8b-instant", streaming=False)
        
        summary_prompt = f"""Summarize the following conversation in 2-3 concise sentences. 
Focus on: key topics discussed, any decisions or conclusions, and important facts mentioned.

Conversation:
{conversation_text}

Summary:"""
        
        result = llm.invoke([HumanMessage(content=summary_prompt)])
        summary = result.content.strip()
        
        # Ensure summary isn't too long
        if len(summary) > 500:
            summary = summary[:497] + "..."
        
        print(f"[ContextManager] Generated summary: {summary[:100]}...", flush=True)
        return summary
        
    except Exception as e:
        print(f"[ContextManager] LLM summarization failed, using fallback: {e}", flush=True)
        # Fallback: extract key points manually
        return _fallback_summary(messages)


def _fallback_summary(messages: list[BaseMessage]) -> str:
    """Simple fallback summary when LLM is unavailable."""
    topics = []
    for msg in messages:
        if isinstance(msg, HumanMessage) and msg.content:
            # Take first 80 chars of each user message as a "topic"
            topic = msg.content[:80].strip()
            if topic:
                topics.append(topic)
    
    if not topics:
        return "Earlier conversation context (details trimmed for context window)."
    
    # Take up to 5 topics
    topic_list = "; ".join(topics[:5])
    return f"Earlier topics discussed: {topic_list}"
