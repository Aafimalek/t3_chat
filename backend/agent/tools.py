"""
Agent Tools - Robust search tool with Tavily (httpx) and article reader.
Based on proven implementation from task-6.
"""

import re
import sys
from typing import Literal, Optional
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup

from config import get_settings


# ============================================================================
# Data Classes for Tool Responses
# ============================================================================

@dataclass
class ToolResponse:
    """Standardized response from tools - never raises exceptions."""
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
    retry_suggestion: Optional[str] = None


@dataclass
class SearchResult:
    """Individual search result."""
    url: str
    title: str
    source: str
    snippet: str
    publication_date: Optional[str] = None
    confidence_hint: str = "MEDIUM"


# ============================================================================
# Search Tool (Tavily via httpx - robust, never throws)
# ============================================================================

class SearchTool:
    """
    Web search using Tavily API via httpx.
    This is tool-only, no LLM reasoning inside.
    Always returns ToolResponse, never throws.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.tavily_api_key
        self.base_url = "https://api.tavily.com"
        self.timeout = 30.0
        self.max_retries = 2
    
    def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "advanced",
        include_answer: bool = True,
        include_domains: Optional[list[str]] = None,
        exclude_domains: Optional[list[str]] = None,
    ) -> ToolResponse:
        """
        Execute a web search. Returns ToolResponse, never throws.
        """
        if not self.api_key:
            return ToolResponse(
                success=False,
                error="TAVILY_API_KEY not configured",
                retry_suggestion="Set TAVILY_API_KEY environment variable"
            )
        
        print(f"[SearchTool] Executing search for: {query}", flush=True)
        print(f"[SearchTool] API key present: {bool(self.api_key)}", flush=True)
        sys.stdout.flush()
        
        for attempt in range(self.max_retries + 1):
            try:
                payload = {
                    "api_key": self.api_key,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": search_depth,
                    "include_answer": include_answer,
                    "include_raw_content": False,
                }
                
                if include_domains:
                    payload["include_domains"] = include_domains
                if exclude_domains:
                    payload["exclude_domains"] = exclude_domains
                
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(
                        f"{self.base_url}/search",
                        json=payload
                    )
                
                print(f"[SearchTool] Response status: {response.status_code}", flush=True)
                
                if response.status_code == 429:
                    return ToolResponse(
                        success=False,
                        error="Rate limit exceeded",
                        retry_suggestion="Wait and retry with fewer queries"
                    )
                
                if response.status_code != 200:
                    if attempt < self.max_retries:
                        continue
                    return ToolResponse(
                        success=False,
                        error=f"API error: {response.status_code}",
                        retry_suggestion="Simplify query or try different search terms"
                    )
                
                data = response.json()
                
                results = []
                answer = data.get("answer")
                
                # Add the generated answer if available
                if answer:
                    results.append({
                        "url": None,
                        "title": "Search Summary",
                        "source": "tavily",
                        "snippet": answer,
                        "publication_date": None,
                        "confidence_hint": "HIGH",
                        "is_summary": True,
                    })
                
                for item in data.get("results", []):
                    confidence = self._assess_confidence(item)
                    
                    results.append({
                        "url": item.get("url", ""),
                        "title": item.get("title", ""),
                        "source": self._extract_domain(item.get("url", "")),
                        "snippet": item.get("content", "")[:800],
                        "publication_date": item.get("published_date"),
                        "confidence_hint": confidence,
                        "is_summary": False,
                    })
                
                search_data = {
                    "query": query,
                    "results": results,
                    "answer": answer,
                }
                
                if not results:
                    return ToolResponse(
                        success=False,
                        error="No results found",
                        retry_suggestion="Try broader or different search terms",
                        data=search_data
                    )
                
                print(f"[SearchTool] Found {len(results)} results", flush=True)
                return ToolResponse(
                    success=True,
                    data=search_data
                )
                
            except httpx.TimeoutException:
                print(f"[SearchTool] Timeout on attempt {attempt + 1}", flush=True)
                if attempt < self.max_retries:
                    continue
                return ToolResponse(
                    success=False,
                    error="Search timeout",
                    retry_suggestion="Simplify query"
                )
            except Exception as e:
                print(f"[SearchTool] Error on attempt {attempt + 1}: {e}", flush=True)
                if attempt < self.max_retries:
                    continue
                return ToolResponse(
                    success=False,
                    error=f"Search failed: {str(e)}",
                    retry_suggestion="Try a different query"
                )
        
        return ToolResponse(
            success=False,
            error="Max retries exceeded",
            retry_suggestion="Try a completely different approach"
        )
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return ""
    
    def _assess_confidence(self, item: dict) -> str:
        """Assess confidence based on source characteristics."""
        url = item.get("url", "").lower()
        
        high_confidence = [
            ".gov", ".edu", "nature.com", "science.org", "arxiv.org",
            "pubmed", "ieee.org", "acm.org", "springer.com",
            "bbc.com", "reuters.com", "apnews.com", "ufc.com",
            "espn.com", "nytimes.com", "washingtonpost.com"
        ]
        
        low_confidence = [
            "reddit.com", "quora.com", "medium.com", "blog",
            "opinion", "forum"
        ]
        
        for domain in high_confidence:
            if domain in url:
                return "HIGH"
        
        for domain in low_confidence:
            if domain in url:
                return "LOW"
        
        return "MEDIUM"


# ============================================================================
# Reader Tool (Article Fetcher & Parser)
# ============================================================================

class ReaderTool:
    """
    Fetches and parses web articles to extract detailed content.
    Useful when snippets don't contain enough detail (e.g., exact dates).
    """
    
    def __init__(self):
        self.timeout = 15.0
        self.max_retries = 2
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
    
    def fetch_article(self, url: str, snippet_fallback: Optional[str] = None) -> ToolResponse:
        """
        Fetch and parse article content. Returns ToolResponse, never throws.
        """
        try:
            result = self._fetch_with_httpx(url)
            if result.success:
                return result
        except Exception:
            pass
        
        # Final fallback: use snippet if available
        if snippet_fallback:
            return ToolResponse(
                success=True,
                data={
                    "url": url,
                    "content": snippet_fallback,
                    "title": "",
                    "extraction_method": "SNIPPET_ONLY"
                }
            )
        
        return ToolResponse(
            success=False,
            error=f"Failed to fetch article: {url}",
            retry_suggestion="Try a different source"
        )
    
    def _fetch_with_httpx(self, url: str) -> ToolResponse:
        """Primary fetch method using httpx + BeautifulSoup."""
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                response = client.get(url, headers=self.headers)
            
            if response.status_code != 200:
                return ToolResponse(
                    success=False,
                    error=f"HTTP {response.status_code}"
                )
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Remove unwanted elements
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()
            
            # Extract title
            title = ""
            if soup.title:
                title = soup.title.string or ""
            elif soup.find("h1"):
                title = soup.find("h1").get_text(strip=True)
            
            # Extract main content
            content = ""
            article_selectors = [
                "article",
                '[role="main"]',
                ".post-content",
                ".article-content",
                ".entry-content",
                ".content",
                "main",
            ]
            
            for selector in article_selectors:
                element = soup.select_one(selector)
                if element:
                    content = element.get_text(separator="\n", strip=True)
                    if len(content) > 200:
                        break
            
            # Fallback to body
            if len(content) < 200:
                body = soup.find("body")
                if body:
                    content = body.get_text(separator="\n", strip=True)
            
            # Clean up content
            lines = [line.strip() for line in content.split("\n") if line.strip()]
            content = "\n".join(lines)
            
            # Truncate if too long
            if len(content) > 10000:
                content = content[:10000] + "...[truncated]"
            
            if len(content) < 100:
                return ToolResponse(
                    success=False,
                    error="Insufficient content extracted"
                )
            
            return ToolResponse(
                success=True,
                data={
                    "url": url,
                    "content": content,
                    "title": title,
                    "extraction_method": "FULL"
                }
            )
            
        except httpx.TimeoutException:
            return ToolResponse(success=False, error="Timeout")
        except Exception as e:
            return ToolResponse(success=False, error=str(e))


# ============================================================================
# Search Heuristics
# ============================================================================

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
    
    # Events and schedules
    r"\b(when is|when's|when will|when does|what date|exact date)\b",
    r"\b(next|upcoming|scheduled|event|fight|match|game)\b",
    r"\b(ufc|nfl|nba|mlb|premier league|champions league)\b",
    
    # Current events and facts
    r"\b(who is|who's) the (current|present)\b",
    r"\b(how much|how many|what is) .* (cost|worth|value)\b",
    r"\b(release date|coming out)\b",
    
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
    """
    if tool_mode == "search":
        return True
    if tool_mode == "none":
        return False
    
    query_lower = query.lower()
    
    for pattern in NO_SEARCH_INDICATORS:
        if re.search(pattern, query_lower):
            return False
    
    for pattern in SEARCH_INDICATORS:
        if re.search(pattern, query_lower):
            return True
    
    return False


# ============================================================================
# Tool Instances
# ============================================================================

_search_tool: SearchTool | None = None
_reader_tool: ReaderTool | None = None


def get_search_tool() -> SearchTool:
    """Get configured search tool instance."""
    global _search_tool
    if _search_tool is None:
        _search_tool = SearchTool()
    return _search_tool


def get_reader_tool() -> ReaderTool:
    """Get configured reader tool instance."""
    global _reader_tool
    if _reader_tool is None:
        _reader_tool = ReaderTool()
    return _reader_tool


# ============================================================================
# Context Building
# ============================================================================

def format_search_context(search_response: ToolResponse, search_requested: bool = False) -> str:
    """
    Format search results as context for the LLM.
    Forces grounded responses by providing explicit instructions.
    """
    if not search_response.success:
        error_msg = search_response.error or "Unknown error"
        if search_requested:
            return (
                f"**WEB SEARCH FAILED**: {error_msg}\n\n"
                "INSTRUCTION: Acknowledge that web search was attempted but failed. "
                "Provide the best answer you can based on your training data, "
                "but clearly state that you could not verify with current sources."
            )
        return f"Search failed: {error_msg}"
    
    data = search_response.data or {}
    query = data.get("query", "")
    results = data.get("results", [])
    
    if not results:
        if search_requested:
            return (
                f"**WEB SEARCH FOR '{query}' RETURNED NO RESULTS**\n\n"
                "INSTRUCTION: Acknowledge that you searched but found no results. "
                "Provide the best answer based on your knowledge while noting this limitation."
            )
        return ""
    
    context_parts = [
        f"**WEB SEARCH RESULTS FOR: \"{query}\"**\n",
        "INSTRUCTION: You MUST use these search results to answer. "
        "Cite specific sources with URLs. Do NOT give generic responses.",
        ""
    ]
    
    for i, result in enumerate(results, 1):
        if result.get("is_summary"):
            context_parts.append(f"### Tavily Summary:\n{result['snippet']}\n")
        else:
            title = result.get("title", f"Result {i}")
            snippet = result.get("snippet", "")
            url = result.get("url", "")
            pub_date = result.get("publication_date")
            confidence = result.get("confidence_hint", "MEDIUM")
            
            context_parts.append(f"### [{i}] {title}")
            if pub_date:
                context_parts.append(f"Published: {pub_date}")
            context_parts.append(f"Confidence: {confidence}")
            if snippet:
                context_parts.append(f"\n{snippet}")
            if url:
                context_parts.append(f"\nSource URL: {url}")
            context_parts.append("")
    
    context_parts.append(
        "\n---\n"
        "IMPORTANT: Base your answer on the information above. "
        "Include specific dates, facts, and cite source URLs. "
        "If information is missing from results, say so explicitly."
    )
    
    return "\n".join(context_parts)


def get_tool_context(
    query: str,
    conversation_id: str | None,
    tool_mode: Literal["auto", "search", "none"] = "auto",
    use_rag: bool = True,
) -> tuple[str, dict]:
    """
    Get combined tool context (search + RAG) for a query.
    """
    print(f"[Tools] get_tool_context called with tool_mode={tool_mode}, use_rag={use_rag}", flush=True)
    print(f"[Tools] Query: {query[:100]}...", flush=True)
    sys.stdout.flush()
    
    context_parts = []
    metadata = {
        "search_used": False,
        "rag_used": False,
        "search_query": None,
        "rag_chunks": 0,
    }
    
    search_explicitly_requested = tool_mode == "search"
    will_search = should_use_search(query, tool_mode)
    print(f"[Tools] Search explicitly requested: {search_explicitly_requested}, Will search: {will_search}", flush=True)
    
    if will_search:
        search_tool = get_search_tool()
        search_response = search_tool.search(query)
        metadata["search_query"] = query
        
        print(f"[Tools] Search response: success={search_response.success}, error={search_response.error}", flush=True)
        
        if search_response.success and search_response.data:
            results = search_response.data.get("results", [])
            print(f"[Tools] Got {len(results)} search results", flush=True)
        
        # When search is explicitly requested, always include context (even on failure)
        if search_explicitly_requested:
            metadata["search_used"] = True
            search_context = format_search_context(search_response, search_requested=True)
            if search_context:
                context_parts.append(search_context)
                
            # If we have results, try to fetch more details from top sources for exact info
            if search_response.success and search_response.data:
                results = search_response.data.get("results", [])
                # Fetch full content from top 2 non-summary results for detailed extraction
                reader_tool = get_reader_tool()
                detailed_parts = []
                
                for result in results[:3]:
                    if result.get("is_summary"):
                        continue
                    url = result.get("url")
                    if not url:
                        continue
                    
                    print(f"[Tools] Fetching detailed content from: {url}", flush=True)
                    article_response = reader_tool.fetch_article(url, result.get("snippet"))
                    
                    if article_response.success and article_response.data:
                        content = article_response.data.get("content", "")
                        if content and len(content) > len(result.get("snippet", "")):
                            # Extract relevant section (first 2000 chars that might contain dates/details)
                            detailed_parts.append(
                                f"\n### Detailed Content from {result.get('title', url)}:\n"
                                f"{content[:2000]}..."
                            )
                    
                    # Only fetch from 2 sources max to avoid timeout
                    if len(detailed_parts) >= 2:
                        break
                
                if detailed_parts:
                    context_parts.append("\n---\n**ADDITIONAL DETAILS FROM SOURCES:**" + "".join(detailed_parts))
        else:
            # Auto mode - only add context if we got good results
            if search_response.success and search_response.data and search_response.data.get("results"):
                search_context = format_search_context(search_response, search_requested=False)
                if search_context:
                    context_parts.append(search_context)
                    metadata["search_used"] = True
    
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
                    chunks = retriever.retrieve(query, conversation_id)
                    metadata["rag_chunks"] = len([c for c in chunks if c.get("score", 0) > 0.3])
        except Exception as e:
            print(f"[Tools] RAG retrieval error: {e}", flush=True)
    
    # Combine contexts
    combined_context = ""
    if context_parts:
        combined_context = "\n\n---\n\n".join(context_parts)
        combined_context = f"\n\n### Tool Results ###\n{combined_context}\n### End Tool Results ###\n"
    
    print(f"[Tools] Final metadata: {metadata}", flush=True)
    sys.stdout.flush()
    
    return combined_context, metadata
