"""
T3.chat Clone Backend - FastAPI Application

A chat API with LangGraph, LangChain-Groq, and MongoDB for:
- Multi-model chat with Groq LLMs
- Short-term memory (conversation context)
- Long-term memory (user facts and preferences)
- Chat persistence
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import close_connections
from routes import chat_router, conversations_router, models_router, rag_router
from routes.users import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    yield
    # Shutdown
    await close_connections()


# Create FastAPI app
app = FastAPI(
    title="T3.chat Clone API",
    description="Chat API with memory and multi-model support",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(chat_router)
app.include_router(conversations_router)
app.include_router(models_router)
app.include_router(users_router)
app.include_router(rag_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "t3-chat-backend"}


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "T3.chat Clone API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
