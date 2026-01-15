"""
RAG Retriever - Query embedding and chunk retrieval with cosine similarity.
"""

import numpy as np
from typing import List

from config import get_settings
from database import get_sync_client
from rag.store import get_embeddings


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a = np.array(vec1)
    b = np.array(vec2)
    
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return dot_product / (norm_a * norm_b)


class RAGRetriever:
    """
    Retrieves relevant chunks from stored documents.
    
    Uses cosine similarity to find the most relevant chunks
    for a given query within a conversation's documents.
    """
    
    def __init__(self):
        settings = get_settings()
        self.client = get_sync_client()
        self.db = self.client[settings.database_name]
        self.chunks_collection = self.db["rag_chunks"]
        self.embeddings = get_embeddings()
        self.top_k = settings.rag_top_k
    
    def retrieve(
        self,
        query: str,
        conversation_id: str,
        top_k: int | None = None,
    ) -> list[dict]:
        """
        Retrieve relevant chunks for a query.
        
        Args:
            query: The user's question
            conversation_id: The conversation to search within
            top_k: Number of results to return (default from settings)
            
        Returns:
            List of relevant chunks with scores
        """
        if top_k is None:
            top_k = self.top_k
        
        # Get all chunks for this conversation
        chunks = list(self.chunks_collection.find(
            {"conversation_id": conversation_id}
        ))
        
        if not chunks:
            return []
        
        # Embed the query
        query_embedding = self.embeddings.embed_query(query)
        
        # Score all chunks
        scored_chunks = []
        for chunk in chunks:
            if "embedding" not in chunk:
                continue
            
            score = cosine_similarity(query_embedding, chunk["embedding"])
            scored_chunks.append({
                "text": chunk["text"],
                "document_id": chunk["document_id"],
                "chunk_index": chunk["chunk_index"],
                "score": float(score),
            })
        
        # Sort by score and return top_k
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        return scored_chunks[:top_k]
    
    def get_context(
        self,
        query: str,
        conversation_id: str,
        top_k: int | None = None,
    ) -> str:
        """
        Get formatted context string for the LLM.
        
        Args:
            query: The user's question
            conversation_id: The conversation to search within
            top_k: Number of chunks to include
            
        Returns:
            Formatted context string or empty string if no relevant chunks
        """
        chunks = self.retrieve(query, conversation_id, top_k)
        
        if not chunks:
            return ""
        
        # Filter out low-scoring chunks
        relevant_chunks = [c for c in chunks if c["score"] > 0.3]
        
        if not relevant_chunks:
            return ""
        
        # Format as context
        context_parts = ["Relevant information from uploaded documents:"]
        for i, chunk in enumerate(relevant_chunks, 1):
            context_parts.append(f"\n[Document excerpt {i}]:\n{chunk['text']}")
        
        return "\n".join(context_parts)


# Singleton instance
_rag_retriever: RAGRetriever | None = None


def get_rag_retriever() -> RAGRetriever:
    """Get the RAG retriever singleton."""
    global _rag_retriever
    if _rag_retriever is None:
        _rag_retriever = RAGRetriever()
    return _rag_retriever
