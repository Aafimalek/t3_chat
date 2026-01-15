"""
Agent Tools - Search tool with Tavily and auto-detection logic.
"""

import re
from typing import Literal

from tavily import TavilyClient

from config import get_settings


# Keywords and patterns that indicate a search might be needed
SEARCH_INDICATORS = [
    # Time-sensitive queries
    r"\b(today|yesterday|this week|this month|this year|202[0-9]|current|latest|recent|now|right now)\b",
    r"\b(what is|what's|what are) .* (price|stock|weather|news|score)\b",
    
    # Real-time information
    r"\b(weather|forecast|temperature)\b.*\b(in|at|for)\b",
    r"\b(news|headlines|latest)\b",
    r"\b(stock|share|market|trading)\b.*\b(price|value)\b",
    r"\b(score|result|match|game)\b.*\b(of|between|vs)\b",
    
    # Current events and facts
    r"\b(who is|who's) the (current|present)\b",
    r"\b(how much|how many|what is) .* (cost|worth|value)\b",
    r"\b(release date|when (will|does|did)|coming out)\b",
    
    # Search-like queries
    r"\b(search|look up|find|google|check)\b",
    r"\b(tell me about|information about|info on)\b",
    r"\b(what happened|what's happening)\b",
]

# Keywords that explicitly suggest NO search needed
NO_SEARCH_INDICATORS = [
    r"\b(explain|teach me|how does .* work|what is the concept)\b",
    r"\b(write|create|generate|make|code|implement)\b",
    r"\b(translate|summarize|rewrite)\b",
    r"\b(my|our|we|I)\b.*(document|pdf|file|upload)",
]


def should_use_search(
    query: str,
    tool_mode: Literal["auto", "search", "none"] = "auto",
) -> bool:
    """
    Determine if search should be used for a query.
    
    Args:
        query: The user's message
        tool_mode: Explicit mode setting from user
            - "search": Always use search
            - "none": Never use search
            - "auto": Use heuristics to decide
            
    Returns:
        True if search should be used
    """
    if tool_mode == "search":
        return True
    if tool_mode == "none":
        return False
    
    # Auto mode - use heuristics
    query_lower = query.lower()
    
    # Check if explicitly about uploaded documents
    for pattern in NO_SEARCH_INDICATORS:
        if re.search(pattern, query_lower):
            return False
    
    # Check for search indicators
    for pattern in SEARCH_INDICATORS:
        if re.search(pattern, query_lower):
            return True
    
    # Default: don't search for most queries
    return False


def run_search(query: str, max_results: int = 5) -> dict:
    """
    Run a Tavily search and return results.
    
    Args:
        query: The search query
        max_results: Maximum number of results
        
    Returns:
        Dict with 'results' list and 'query' string
    """
    settings = get_settings()
    
    if not settings.tavily_api_key:
        return {
            "query": query,
            "results": [],
            "error": "Tavily API key not configured",
        }
    
    try:
        client = TavilyClient(api_key=settings.tavily_api_key)
        
        # Use search with answer generation for better results
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_answer=True,
            include_raw_content=False,
        )
        
        results = []
        
        # Add the AI-generated answer if available
        if response.get("answer"):
            results.append({
                "title": "Summary",
                "content": response["answer"],
                "url": None,
                "is_summary": True,
            })
        
        # Add individual search results
        for result in response.get("results", []):
            results.append({
                "title": result.get("title", ""),
                "content": result.get("content", ""),
                "url": result.get("url", ""),
                "is_summary": False,
            })
        
        return {
            "query": query,
            "results": results,
            "success": True,
        }
        
    except Exception as e:
        return {
            "query": query,
            "results": [],
            "error": str(e),
            "success": False,
        }


def format_search_context(search_results: dict) -> str:
    """
    Format search results as context for the LLM.
    
    Args:
        search_results: Output from run_search()
        
    Returns:
        Formatted context string
    """
    if not search_results.get("results"):
        if search_results.get("error"):
            return f"Search failed: {search_results['error']}"
        return ""
    
    context_parts = [f"Web search results for: \"{search_results['query']}\""]
    
    for i, result in enumerate(search_results["results"], 1):
        if result.get("is_summary"):
            context_parts.append(f"\n**Search Summary:**\n{result['content']}")
        else:
            title = result.get("title", f"Result {i}")
            content = result.get("content", "")
            url = result.get("url", "")
            
            context_parts.append(f"\n[{i}] {title}")
            if content:
                # Truncate very long content
                if len(content) > 500:
                    content = content[:500] + "..."
                context_parts.append(content)
            if url:
                context_parts.append(f"Source: {url}")
    
    return "\n".join(context_parts)


def get_tool_context(
    query: str,
    conversation_id: str | None,
    tool_mode: Literal["auto", "search", "none"] = "auto",
    use_rag: bool = True,
) -> tuple[str, dict]:
    """
    Get combined tool context (search + RAG) for a query.
    
    Args:
        query: The user's message
        conversation_id: Current conversation ID
        tool_mode: Search mode setting
        use_rag: Whether to include RAG context
        
    Returns:
        Tuple of (context_string, metadata_dict)
    """
    context_parts = []
    metadata = {
        "search_used": False,
        "rag_used": False,
        "search_query": None,
        "rag_chunks": 0,
    }
    
    # Check if search should be used
    if should_use_search(query, tool_mode):
        search_results = run_search(query)
        if search_results.get("success") and search_results.get("results"):
            search_context = format_search_context(search_results)
            if search_context:
                context_parts.append(search_context)
                metadata["search_used"] = True
                metadata["search_query"] = query
    
    # Get RAG context if conversation has documents
    if use_rag and conversation_id:
        try:
            from rag.retriever import get_rag_retriever
            from rag.store import get_rag_store
            
            store = get_rag_store()
            if store.has_documents(conversation_id):
                retriever = get_rag_retriever()
                rag_context = retriever.get_context(query, conversation_id)
                if rag_context:
                    context_parts.append(rag_context)
                    metadata["rag_used"] = True
                    # Count chunks from the retriever
                    chunks = retriever.retrieve(query, conversation_id)
                    metadata["rag_chunks"] = len([c for c in chunks if c["score"] > 0.3])
        except Exception as e:
            print(f"RAG retrieval error: {e}")
    
    # Combine contexts
    combined_context = ""
    if context_parts:
        combined_context = "\n\n---\n\n".join(context_parts)
        combined_context = f"\n\n### Tool Results ###\n{combined_context}\n### End Tool Results ###\n"
    
    return combined_context, metadata
