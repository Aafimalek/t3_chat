"""
RAG (Retrieval-Augmented Generation) endpoints for PDF upload and management.
"""

import uuid
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form
from pydantic import BaseModel

# Import RAG store with error handling
_rag_store_error = None
try:
    from rag.store import get_rag_store
    print("[RAG Router] Successfully imported RAG store")
except Exception as e:
    _rag_store_error = str(e)
    print(f"[RAG Router] ERROR importing RAG store: {e}")
    import traceback
    traceback.print_exc()
    
    # Define a dummy function to avoid NameError
    def get_rag_store():
        raise RuntimeError(f"RAG store failed to initialize: {_rag_store_error}")


router = APIRouter(prefix="/api/rag", tags=["RAG"])


@router.get("/test")
async def test_rag_route():
    """Simple test endpoint to verify RAG router is working."""
    print("[RAG Test] Test endpoint hit!", flush=True)
    return {"status": "ok", "message": "RAG router is working"}


# ============================================================================
# Response Models
# ============================================================================

class DocumentUploadResponse(BaseModel):
    """Response from document upload."""
    document_id: str
    conversation_id: str
    filename: str
    chunk_count: int
    text_length: int
    message: str


class DocumentInfo(BaseModel):
    """Information about a stored document."""
    document_id: str
    filename: str
    chunk_count: int
    text_length: int
    created_at: str


class DocumentListResponse(BaseModel):
    """Response for document listing."""
    documents: list[DocumentInfo]
    conversation_id: str
    total: int


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    conversation_id: str | None = Form(default=None),
):
    """
    Upload a PDF document for RAG.
    
    The document will be:
    - Stored in MongoDB (GridFS)
    - Text extracted and chunked
    - Embeddings generated and stored
    
    If no conversation_id is provided, a new one will be created.
    """
    import traceback
    
    try:
        # Log incoming request
        print(f"[RAG Upload] Received upload request:", flush=True)
        print(f"  - filename: {file.filename}", flush=True)
        print(f"  - user_id: {user_id}", flush=True)
        print(f"  - conversation_id: {conversation_id or '(will create new)'}", flush=True)
    except Exception as e:
        print(f"[RAG Upload] Error logging request: {e}", flush=True)
        traceback.print_exc()
    
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )
    
    # Read file content
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to read file: {str(e)}"
        )
    
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    
    # Store document
    try:
        store = get_rag_store()
        result = store.store_document(
            file_content=content,
            filename=file.filename,
            user_id=user_id,
            conversation_id=conversation_id,
        )
        
        return DocumentUploadResponse(
            document_id=result["document_id"],
            conversation_id=result["conversation_id"],
            filename=result["filename"],
            chunk_count=result["chunk_count"],
            text_length=result["text_length"],
            message="Document uploaded and processed successfully",
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document: {str(e)}"
        )


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    user_id: str = Query(..., description="User identifier"),
    conversation_id: str = Query(..., description="Conversation identifier"),
):
    """
    List all documents uploaded to a conversation.
    """
    try:
        store = get_rag_store()
        documents = store.get_documents(conversation_id, user_id)
        
        return DocumentListResponse(
            documents=[DocumentInfo(**doc) for doc in documents],
            conversation_id=conversation_id,
            total=len(documents),
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    user_id: str = Query(..., description="User identifier"),
):
    """
    Delete a document and its embeddings.
    """
    try:
        store = get_rag_store()
        success = store.delete_document(document_id, user_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Document not found or access denied"
            )
        
        return {
            "message": "Document deleted successfully",
            "document_id": document_id,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.get("/documents/{conversation_id}/count")
async def get_document_count(
    conversation_id: str,
    user_id: str = Query(..., description="User identifier"),
):
    """
    Get the count of documents in a conversation.
    Quick check without loading all document details.
    """
    try:
        store = get_rag_store()
        documents = store.get_documents(conversation_id, user_id)
        
        return {
            "conversation_id": conversation_id,
            "count": len(documents),
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get document count: {str(e)}"
        )
