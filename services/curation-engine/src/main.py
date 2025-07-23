"""
Curation Engine Service
Intelligent content curation, recommendation, and quality assessment for fashion generation
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging
from typing import Optional

from .core.config import get_settings
from .core.redis_client import get_redis_client
from .api.routes import health
from .api.routes.curation import router as curation_router
from .services.recommendation_engine import RecommendationEngine
from .services.quality_assessor import QualityAssessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global service instances
recommendation_engine: Optional[RecommendationEngine] = None
quality_assessor: Optional[QualityAssessor] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    global recommendation_engine, quality_assessor
    
    # Startup
    logger.info("Starting Curation Engine Service...")
    settings = get_settings()
    
    try:
        # Initialize quality assessor
        quality_assessor = QualityAssessor()
        await quality_assessor.initialize()
        logger.info("Quality assessor initialized")
        
        # Initialize recommendation engine
        recommendation_engine = RecommendationEngine()
        await recommendation_engine.initialize()
        logger.info("Recommendation engine initialized")
        
        logger.info("Curation Engine services initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down Curation Engine...")
        
        if quality_assessor:
            await quality_assessor.cleanup()
        if recommendation_engine:
            await recommendation_engine.cleanup()
        
        logger.info("Curation Engine shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Curation Engine Service",
    description="Intelligent content curation and recommendation for fashion generation",
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
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(curation_router, prefix="/api/v1/curation", tags=["curation"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Curation Engine Service",
        "version": "1.0.0",
        "status": "operational",
        "description": "Intelligent content curation and recommendation for fashion generation"
    }


# Dependency providers
async def get_recommendation_engine() -> RecommendationEngine:
    """Get recommendation engine instance."""
    if recommendation_engine is None:
        raise HTTPException(status_code=503, detail="Recommendation engine not initialized")
    return recommendation_engine


async def get_quality_assessor() -> QualityAssessor:
    """Get quality assessor instance."""
    if quality_assessor is None:
        raise HTTPException(status_code=503, detail="Quality assessor not initialized")
    return quality_assessor
        raise HTTPException(status_code=503, detail="Recommendation engine not initialized")
    return recommendation_engine


async def get_quality_assessor() -> QualityAssessor:
    """Get quality assessor instance."""
    if quality_assessor is None:
        raise HTTPException(status_code=503, detail="Quality assessor not initialized")
    return quality_assessor


