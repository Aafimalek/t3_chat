"""
Memory Manager - Orchestrates short-term and long-term memory operations.
"""

from datetime import datetime
from typing import Any
import uuid

from memory.store import get_memory_store


class MemoryManager:
    """
    Manages memory operations for the chat agent.
    
    Responsibilities:
    - Store and retrieve long-term memories
    - Manage memory namespaces per user
    - Extract and save important facts from conversations
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.store = get_memory_store()
        self.namespace = ("user_memories", user_id)
    
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
        """List all memories for the user."""
        return list(self.store.search(namespace_prefix=self.namespace, limit=limit))
    
    def delete_memory(self, key: str) -> None:
        """Delete a specific memory."""
        self.store.delete(namespace=self.namespace, key=key)
    
    def save_fact(self, fact: str, source: str = "conversation") -> str:
        """
        Save a fact learned about the user.
        
        Args:
            fact: The fact to remember
            source: Where this fact was learned
            
        Returns:
            The key under which the fact was stored
        """
        key = f"fact_{uuid.uuid4().hex[:8]}"
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
    
    def get_context_memories(self, query: str, limit: int = 5) -> str:
        """
        Get memories formatted as context for the LLM.
        
        Args:
            query: The current user message (not used for now, just returns recent memories)
            limit: Maximum number of memories to retrieve
            
        Returns:
            Formatted string of relevant memories
        """
        try:
            # Just list recent memories for now
            memories = self.list_memories(limit=limit)
            
            if not memories:
                return ""
            
            memory_texts = []
            for item in memories:
                value = item.value if hasattr(item, 'value') else item.get('value', {})
                if isinstance(value, dict):
                    if value.get("type") == "fact":
                        memory_texts.append(f"- {value.get('content', '')}")
                    elif value.get("type") == "preference":
                        memory_texts.append(
                            f"- User preference ({value.get('category', 'general')}): "
                            f"{value.get('value', '')}"
                        )
            
            if not memory_texts:
                return ""
            
            return "Relevant memories about the user:\n" + "\n".join(memory_texts)
        except Exception:
            # If memory retrieval fails, just continue without memories
            return ""
