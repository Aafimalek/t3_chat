"""
Memory Manager - Orchestrates short-term and long-term memory operations.
"""

import json
import hashlib
from datetime import datetime
from typing import Any
import uuid

from memory.store import get_memory_store
from database import get_sync_client
from config import get_settings


class MemoryManager:
    """
    Manages memory operations for the chat agent.
    
    Responsibilities:
    - Store and retrieve long-term memories
    - Manage memory namespaces per user
    - Extract and save important facts from conversations
    - Deduplicate facts to avoid redundancy
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.store = get_memory_store()
        self.namespace = ("user_memories", user_id)
        # Direct MongoDB access for queries that don't work with the store API
        settings = get_settings()
        self._db = get_sync_client()[settings.database_name]
        self._collection = self._db["memory_store"]
    
    def save_memory(self, key: str, value: dict[str, Any]) -> None:
        """Save a memory item to the store."""
        self.store.put(
            namespace=self.namespace,
            key=key,
            value=value,
        )
    
    def get_memory(self, key: str) -> Any:
        """Retrieve a specific memory item."""
        return self.store.get(namespace=self.namespace, key=key)
    
    def list_memories(self, limit: int = 100) -> list:
        """List all memories for the user using direct MongoDB query."""
        try:
            # Use direct MongoDB query since store.search() has issues
            namespace_list = list(self.namespace)
            cursor = self._collection.find(
                {"namespace": namespace_list}
            ).limit(limit)
            
            results = []
            for doc in cursor:
                # Create a simple object with key and value attributes
                class MemoryItem:
                    def __init__(self, key, value):
                        self.key = key
                        self.value = value
                
                results.append(MemoryItem(doc.get("key"), doc.get("value", {})))
            
            return results
        except Exception as e:
            print(f"Error listing memories: {e}")
            return []
    
    def delete_memory(self, key: str) -> None:
        """Delete a specific memory."""
        self.store.delete(namespace=self.namespace, key=key)
    
    def _get_fact_hash(self, fact: str) -> str:
        """Generate a consistent hash for a fact to enable deduplication."""
        # Normalize the fact for comparison
        normalized = fact.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()[:12]
    
    def _is_duplicate_fact(self, fact: str, existing_memories: list) -> bool:
        """Check if a similar fact already exists."""
        fact_lower = fact.lower().strip()
        
        for item in existing_memories:
            value = item.value if hasattr(item, 'value') else item.get('value', {})
            if isinstance(value, dict) and value.get("type") in ("fact", "core_fact"):
                existing_content = value.get("content", "").lower().strip()
                # Check for exact match or high similarity
                if existing_content == fact_lower:
                    return True
                # Check if one contains the other (update scenario)
                if fact_lower in existing_content or existing_content in fact_lower:
                    return True
        return False
    
    def save_fact(self, fact: str, source: str = "conversation") -> str | None:
        """
        Save a fact learned about the user with deduplication.
        
        Args:
            fact: The fact to remember
            source: Where this fact was learned
            
        Returns:
            The key under which the fact was stored, or None if duplicate
        """
        # Check for duplicates
        existing = self.list_memories(limit=50)
        if self._is_duplicate_fact(fact, existing):
            return None
        
        # Use hash-based key for implicit deduplication
        fact_hash = self._get_fact_hash(fact)
        key = f"fact_{fact_hash}"
        
        self.save_memory(
            key=key,
            value={
                "type": "fact",
                "content": fact,
                "source": source,
                "created_at": datetime.utcnow().isoformat(),
            }
        )
        return key
    
    def save_facts_batch(self, facts: list[str], source: str = "conversation") -> list[str]:
        """
        Save multiple facts with deduplication.
        
        Args:
            facts: List of facts to save
            source: Where these facts were learned
            
        Returns:
            List of keys for newly saved facts
        """
        saved_keys = []
        for fact in facts:
            if fact and len(fact.strip()) > 3:  # Skip very short "facts"
                key = self.save_fact(fact.strip(), source)
                if key:
                    saved_keys.append(key)
        return saved_keys
    
    def save_preference(self, category: str, preference: str) -> str:
        """
        Save a user preference.
        
        Args:
            category: Category of preference (e.g., "communication_style")
            preference: The preference value
            
        Returns:
            The key under which the preference was stored
        """
        key = f"pref_{category}"
        self.save_memory(
            key=key,
            value={
                "type": "preference",
                "category": category,
                "value": preference,
                "updated_at": datetime.utcnow().isoformat(),
            }
        )
        return key
    
    def get_all_facts(self) -> list[str]:
        """Get all facts as a list of strings."""
        memories = self.list_memories(limit=100)
        facts = []
        for item in memories:
            value = item.value if hasattr(item, 'value') else item.get('value', {})
            if isinstance(value, dict) and value.get("type") in ("fact", "core_fact"):
                facts.append(value.get("content", ""))
        return facts
    
    def get_context_memories(self, query: str, limit: int = 10) -> str:
        """
        Get memories formatted as context for the LLM.
        
        Args:
            query: The current user message (for potential future relevance filtering)
            limit: Maximum number of memories to retrieve
            
        Returns:
            Formatted string of relevant memories
        """
        try:
            memories = self.list_memories(limit=limit)
            
            if not memories:
                return ""
            
            memory_texts = []
            for item in memories:
                value = item.value if hasattr(item, 'value') else item.get('value', {})
                if isinstance(value, dict):
                    mem_type = value.get("type", "")
                    # Include both regular facts and core facts from settings
                    if mem_type in ("fact", "core_fact"):
                        content = value.get('content', '')
                        if content:
                            memory_texts.append(f"- {content}")
                    elif mem_type == "preference":
                        memory_texts.append(
                            f"- User preference ({value.get('category', 'general')}): "
                            f"{value.get('value', '')}"
                        )
            
            if not memory_texts:
                return ""
            
            return "Things I remember about you:\n" + "\n".join(memory_texts)
        except Exception as e:
            print(f"Error getting context memories: {e}")
            return ""
    
    def clear_all_memories(self) -> int:
        """Clear all memories for this user. Returns count of deleted items."""
        memories = self.list_memories(limit=1000)
        count = 0
        for item in memories:
            key = item.key if hasattr(item, 'key') else item.get('key')
            if key:
                self.delete_memory(key)
                count += 1
        return count


def extract_facts_from_response(llm_response: str) -> list[str]:
    """
    Parse the LLM's fact extraction response.
    
    Args:
        llm_response: The raw LLM response (should be JSON array)
        
    Returns:
        List of extracted facts
    """
    try:
        # Clean up the response
        response = llm_response.strip()
        
        # Handle common formatting issues
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        
        response = response.strip()
        
        # Parse JSON
        facts = json.loads(response)
        
        if isinstance(facts, list):
            return [str(f) for f in facts if f and isinstance(f, str)]
        return []
    except (json.JSONDecodeError, ValueError):
        return []
