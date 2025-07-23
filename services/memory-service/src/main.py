"""
KSE Memory Service
Dedicated microservice for Knowledge-State-Experience memory operations
Handles temporal knowledge graphs, vector embeddings, and memory retrieval
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging
from typing import List, Optional

from .core.config import get_settings
from .core.database import get_db, init_db
from .core.redis_client import get_redis_client
from .api.routes import memory, knowledge_graph, embeddings, health
from .services.memory_manager import MemoryManager
from .services.knowledge_graph_service import KnowledgeGraphService
from .services.embedding_service import EmbeddingService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global service instances
memory_manager: Optional[MemoryManager] = None
knowledge_graph_service: Optional[KnowledgeGraphService] = None
embedding_service: Optional[EmbeddingService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    global memory_manager, knowledge_graph_service, embedding_service
    
    # Startup
    logger.info("Starting KSE Memory Service...")
    settings = get_settings()
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Initialize embedding service
    embedding_service = EmbeddingService()
    await embedding_service.initialize()
    logger.info("Embedding service initialized")
    
    # Initialize knowledge graph service
    knowledge_graph_service = KnowledgeGraphService()
    await knowledge_graph_service.initialize()
    logger.info("Knowledge graph service initialized")
    
    # Initialize memory manager
    memory_manager = MemoryManager(embedding_service, knowledge_graph_service)
    await memory_manager.initialize()
    logger.info("Memory manager initialized")
    
    logger.info("KSE Memory Service startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down KSE Memory Service...")
    if memory_manager:
        await memory_manager.cleanup()
    if knowledge_graph_service:
        await knowledge_graph_service.cleanup()
    if embedding_service:
        await embedding_service.cleanup()
    logger.info("KSE Memory Service shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="KSE Memory Service",
    description="Knowledge-State-Experience memory operations for GEN-VIEW-KSE",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(memory.router, prefix="/api/v1/memory", tags=["memory"])
app.include_router(knowledge_graph.router, prefix="/api/v1/knowledge-graph", tags=["knowledge-graph"])
app.include_router(embeddings.router, prefix="/api/v1/embeddings", tags=["embeddings"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "KSE Memory Service",
        "version": "1.0.0",
        "status": "operational",
        "description": "Knowledge-State-Experience memory operations"
    }


# Dependency providers
async def get_memory_manager() -> MemoryManager:
    """Get memory manager instance."""
    if memory_manager is None:
        raise HTTPException(status_code=503, detail="Memory manager not initialized")
    return memory_manager


async def get_knowledge_graph_service() -> KnowledgeGraphService:
    """Get knowledge graph service instance."""
    if knowledge_graph_service is None:
        raise HTTPException(status_code=503, detail="Knowledge graph service not initialized")
    return knowledge_graph_service


async def get_embedding_service() -> EmbeddingService:
    """Get embedding service instance."""
    if embedding_service is None:
        raise HTTPException(status_code=503, detail="Embedding service not initialized")
    return embedding_service