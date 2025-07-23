"""
GEN-VIEW-KSE Generation API Service
Main FastAPI application with async/await patterns for high-throughput AI model serving
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
from .api.routes import generation, health, collections
from .services.model_manager import ModelManager
from .services.generation_service import GenerationService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global model manager instance
model_manager: Optional[ModelManager] = None
generation_service: Optional[GenerationService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    global model_manager, generation_service
    
    # Startup
    logger.info("Starting GEN-VIEW-KSE Generation API...")
    settings = get_settings()
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Initialize model manager
    model_manager = ModelManager()
    await model_manager.initialize()
    logger.info("AI models loaded and ready")
    
    # Initialize generation service
    generation_service = GenerationService(model_manager)
    logger.info("Generation service initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down GEN-VIEW-KSE Generation API...")
    if model_manager:
        await model_manager.cleanup()
    logger.info("Cleanup completed")


# Create FastAPI application
app = FastAPI(
    title="GEN-VIEW-KSE Generation API",
    description="AI-powered fashion generation service with KSE substrate integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(generation.router, prefix="/api/v1/generation", tags=["generation"])
app.include_router(collections.router, prefix="/api/v1/collections", tags=["collections"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "GEN-VIEW-KSE Generation API",
        "version": "1.0.0",
        "description": "AI-powered fashion generation service with KSE substrate integration",
        "docs_url": "/docs",
        "health_check": "/health"
    }


# Dependency injection for services
def get_model_manager() -> ModelManager:
    """Get the global model manager instance."""
    if model_manager is None:
        raise HTTPException(status_code=503, detail="Model manager not initialized")
    return model_manager


def get_generation_service() -> GenerationService:
    """Get the global generation service instance."""
    if generation_service is None:
        raise HTTPException(status_code=503, detail="Generation service not initialized")
    return generation_service


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )