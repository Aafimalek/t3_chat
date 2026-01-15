"""
RAG Document Store - PDF ingestion, chunking, embeddings, and MongoDB storage.
Stores PDFs and vector embeddings scoped to conversations.
"""

import io
import uuid
from datetime import datetime
from typing import BinaryIO

import pdfplumber
import numpy as np
from gridfs import GridFS
from langchain_ollama import OllamaEmbeddings

from config import get_settings
from database import get_sync_client


def get_embeddings() -> OllamaEmbeddings:
    """Get Ollama embeddings instance."""
    settings = get_settings()
    return OllamaEmbeddings(
        base_url=settings.ollama_base_url,
        model=settings.ollama_embed_model,
    )


def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF using pdfplumber."""
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_content)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n\n".join(text_parts)


def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[dict]:
    """
    Split text into overlapping chunks.
    
    Returns list of dicts with 'text' and 'index' keys.
    """
    if not text:
        return []
    
    chunks = []
    start = 0
    index = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk_text_content = text[start:end]
        
        # Try to break at sentence boundary if possible
        if end < len(text):
            # Look for sentence end within last 100 chars
            last_period = chunk_text_content.rfind('. ')
            last_newline = chunk_text_content.rfind('\n')
            break_point = max(last_period, last_newline)
            
            if break_point > chunk_size * 0.7:  # Only break if we have enough content
                chunk_text_content = chunk_text_content[:break_point + 1]
                end = start + break_point + 1
        
        chunks.append({
            "text": chunk_text_content.strip(),
            "index": index,
        })
        
        index += 1
        start = end - chunk_overlap
        
        # Prevent infinite loop
        if start >= len(text) - chunk_overlap:
            break
    
    return chunks


class RAGStore:
    """
    Manages RAG document storage and retrieval.
    
    - Stores PDFs in GridFS
    - Stores document metadata in rag_documents collection
    - Stores chunk embeddings in rag_chunks collection
    """
    
    def __init__(self):
        settings = get_settings()
        self.client = get_sync_client()
        self.db = self.client[settings.database_name]
        self.fs = GridFS(self.db, collection="rag_files")
        self.documents_collection = self.db["rag_documents"]
        self.chunks_collection = self.db["rag_chunks"]
        self.embeddings = get_embeddings()
        self.settings = settings
        
        # Create indexes for efficient queries
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Create necessary indexes."""
        self.documents_collection.create_index([
            ("conversation_id", 1),
            ("user_id", 1),
        ])
        self.chunks_collection.create_index([
            ("conversation_id", 1),
            ("document_id", 1),
        ])
    
    def store_document(
        self,
        file_content: bytes,
        filename: str,
        user_id: str,
        conversation_id: str | None = None,
    ) -> dict:
        """
        Store a PDF document with its embeddings.
        
        Args:
            file_content: PDF file bytes
            filename: Original filename
            user_id: User identifier
            conversation_id: Optional conversation ID (creates new if None)
            
        Returns:
            Document metadata including document_id and conversation_id
        """
        # Generate IDs
        document_id = str(uuid.uuid4())
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        # Extract text from PDF
        text = extract_text_from_pdf(file_content)
        if not text.strip():
            raise ValueError("Could not extract text from PDF")
        
        # Store PDF in GridFS
        file_id = self.fs.put(
            file_content,
            filename=filename,
            document_id=document_id,
            user_id=user_id,
            conversation_id=conversation_id,
        )
        
        # Chunk the text
        chunks = chunk_text(
            text,
            chunk_size=self.settings.rag_chunk_size,
            chunk_overlap=self.settings.rag_chunk_overlap,
        )
        
        # Generate embeddings for all chunks
        chunk_texts = [c["text"] for c in chunks]
        embeddings = self.embeddings.embed_documents(chunk_texts)
        
        # Store document metadata
        doc_metadata = {
            "_id": document_id,
            "filename": filename,
            "user_id": user_id,
            "conversation_id": conversation_id,
            "file_id": file_id,
            "chunk_count": len(chunks),
            "text_length": len(text),
            "created_at": datetime.utcnow(),
        }
        self.documents_collection.insert_one(doc_metadata)
        
        # Store chunks with embeddings
        chunk_docs = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_docs.append({
                "_id": f"{document_id}_chunk_{i}",
                "document_id": document_id,
                "conversation_id": conversation_id,
                "user_id": user_id,
                "chunk_index": chunk["index"],
                "text": chunk["text"],
                "embedding": embedding,
                "created_at": datetime.utcnow(),
            })
        
        if chunk_docs:
            self.chunks_collection.insert_many(chunk_docs)
        
        return {
            "document_id": document_id,
            "conversation_id": conversation_id,
            "filename": filename,
            "chunk_count": len(chunks),
            "text_length": len(text),
        }
    
    def get_documents(self, conversation_id: str, user_id: str) -> list[dict]:
        """Get all documents for a conversation."""
        cursor = self.documents_collection.find({
            "conversation_id": conversation_id,
            "user_id": user_id,
        }).sort("created_at", -1)
        
        return [
            {
                "document_id": doc["_id"],
                "filename": doc["filename"],
                "chunk_count": doc["chunk_count"],
                "text_length": doc["text_length"],
                "created_at": doc["created_at"].isoformat(),
            }
            for doc in cursor
        ]
    
    def delete_document(self, document_id: str, user_id: str) -> bool:
        """Delete a document and its chunks."""
        # Verify ownership
        doc = self.documents_collection.find_one({
            "_id": document_id,
            "user_id": user_id,
        })
        
        if not doc:
            return False
        
        # Delete from GridFS
        if doc.get("file_id"):
            self.fs.delete(doc["file_id"])
        
        # Delete chunks
        self.chunks_collection.delete_many({"document_id": document_id})
        
        # Delete document metadata
        self.documents_collection.delete_one({"_id": document_id})
        
        return True
    
    def has_documents(self, conversation_id: str) -> bool:
        """Check if a conversation has any RAG documents."""
        return self.documents_collection.count_documents(
            {"conversation_id": conversation_id}
        ) > 0


# Singleton instance
_rag_store: RAGStore | None = None


def get_rag_store() -> RAGStore:
    """Get the RAG store singleton."""
    global _rag_store
    if _rag_store is None:
        _rag_store = RAGStore()
    return _rag_store
