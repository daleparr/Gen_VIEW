"""
NeRF Rendering Service
Handles 3D visualization, NeRF rendering, and fashion product visualization
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
from .api.routes import rendering, nerf, health, visualization
from .services.rendering_manager import RenderingManager
from .services.nerf_service import NeRFService
from .services.mesh_processor import MeshProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global service instances
rendering_manager: Optional[RenderingManager] = None
nerf_service: Optional[NeRFService] = None
mesh_processor: Optional[MeshProcessor] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    global rendering_manager, nerf_service, mesh_processor
    
    # Startup
    logger.info("Starting NeRF Rendering Service...")
    settings = get_settings()
    
    # Initialize mesh processor
    mesh_processor = MeshProcessor()
    await mesh_processor.initialize()
    logger.info("Mesh processor initialized")
    
    # Initialize NeRF service
    nerf_service = NeRFService()
    await nerf_service.initialize()
    logger.info("NeRF service initialized")
    
    # Initialize rendering manager
    rendering_manager = RenderingManager(nerf_service, mesh_processor)
    await rendering_manager.initialize()
    logger.info("Rendering manager initialized")
    
    logger.info("NeRF Rendering Service startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down NeRF Rendering Service...")
    if rendering_manager:
        await rendering_manager.cleanup()
    if nerf_service:
        await nerf_service.cleanup()
    if mesh_processor:
        await mesh_processor.cleanup()
    logger.info("NeRF Rendering Service shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="NeRF Rendering Service",
    description="3D visualization and NeRF rendering for GEN-VIEW-KSE",
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
app.include_router(rendering.router, prefix="/api/v1/render", tags=["rendering"])
app.include_router(nerf.router, prefix="/api/v1/nerf", tags=["nerf"])
app.include_router(visualization.router, prefix="/api/v1/visualize", tags=["visualization"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "NeRF Rendering Service",
        "version": "1.0.0",
        "status": "operational",
        "description": "3D visualization and NeRF rendering for fashion products"
    }


# Dependency providers
async def get_rendering_manager() -> RenderingManager:
    """Get rendering manager instance."""
    if rendering_manager is None:
        raise HTTPException(status_code=503, detail="Rendering manager not initialized")
    return rendering_manager


async def get_nerf_service() -> NeRFService:
    """Get NeRF service instance."""
    if nerf_service is None:
        raise HTTPException(status_code=503, detail="NeRF service not initialized")
    return nerf_service


async def get_mesh_processor() -> MeshProcessor:
    """Get mesh processor instance."""
    if mesh_processor is None:
        raise HTTPException(status_code=503, detail="Mesh processor not initialized")
    return mesh_processor