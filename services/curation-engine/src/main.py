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
from .api.routes import curation, recommendation, quality, health, trends
from .services.curation_manager import CurationManager
from .services.recommendation_engine import RecommendationEngine
from .services.quality_assessor import QualityAssessor
from .services.trend_analyzer import TrendAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global service instances
curation_manager: Optional[CurationManager] = None
recommendation_engine: Optional[RecommendationEngine] = None
quality_assessor: Optional[QualityAssessor] = None
trend_analyzer: Optional[TrendAnalyzer] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    global curation_manager, recommendation_engine, quality_assessor, trend_analyzer
    
    # Startup
    logger.info("Starting Curation Engine Service...")
    settings = get_settings()
    
    # Initialize quality assessor
    quality_assessor = QualityAssessor()
    await quality_assessor.initialize()
    logger.info("Quality assessor initialized")
    
    # Initialize trend analyzer
    trend_analyzer = TrendAnalyzer()
    await trend_analyzer.initialize()
    logger.info("Trend analyzer initialized")
    
    # Initialize recommendation engine
    recommendation_engine = RecommendationEngine(quality_assessor, trend_analyzer)
    await recommendation_engine.initialize()
    logger.info("Recommendation engine initialized")
    
    # Initialize curation manager
    curation_manager = CurationManager(recommendation_engine, quality_assessor, trend_analyzer)
    await curation_manager.initialize()
    logger.info("Curation manager initialized")
    
    logger.info("Curation Engine Service startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Curation Engine Service...")
    if curation_manager:
        await curation_manager.cleanup()
    if recommendation_engine:
        await recommendation_engine.cleanup()
    if quality_assessor:
        await quality_assessor.cleanup()
    if trend_analyzer:
        await trend_analyzer.cleanup()
    logger.info("Curation Engine Service shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Curation Engine Service",
    description="Intelligent content curation and recommendation for GEN-VIEW-KSE",
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
app.include_router(curation.router, prefix="/api/v1/curate", tags=["curation"])
app.include_router(recommendation.router, prefix="/api/v1/recommend", tags=["recommendation"])
app.include_router(quality.router, prefix="/api/v1/quality", tags=["quality"])
app.include_router(trends.router, prefix="/api/v1/trends", tags=["trends"])


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
async def get_curation_manager() -> CurationManager:
    """Get curation manager instance."""
    if curation_manager is None:
        raise HTTPException(status_code=503, detail="Curation manager not initialized")
    return curation_manager


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


async def get_trend_analyzer() -> TrendAnalyzer:
    """Get trend analyzer instance."""
    if trend_analyzer is None:
        raise HTTPException(status_code=503, detail="Trend analyzer not initialized")
    return trend_analyzer