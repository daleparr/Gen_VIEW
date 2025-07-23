"""
Health check routes for NeRF Rendering Service
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import logging

from ...core.redis_client import get_rendering_queue
from ...main import get_rendering_manager, get_nerf_service, get_mesh_processor

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "service": "NeRF Rendering Service",
        "status": "healthy",
        "timestamp": "2025-01-23T08:00:00Z"
    }


@router.get("/detailed")
async def detailed_health_check(
    rendering_manager=Depends(get_rendering_manager),
    nerf_service=Depends(get_nerf_service),
    mesh_processor=Depends(get_mesh_processor)
) -> Dict[str, Any]:
    """Detailed health check with component status."""
    try:
        health_data = {
            "service": "NeRF Rendering Service",
            "status": "healthy",
            "timestamp": "2025-01-23T08:00:00Z",
            "components": {}
        }
        
        # Check Redis queue
        try:
            rendering_queue = await get_rendering_queue()
            queue_healthy = await rendering_queue.health_check()
            queue_stats = await rendering_queue.get_queue_stats()
            
            health_data["components"]["redis_queue"] = {
                "status": "healthy" if queue_healthy else "unhealthy",
                "connected": queue_healthy,
                "stats": queue_stats
            }
        except Exception as e:
            health_data["components"]["redis_queue"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Check NeRF service
        try:
            nerf_health = await nerf_service.health_check()
            health_data["components"]["nerf_service"] = nerf_health
        except Exception as e:
            health_data["components"]["nerf_service"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Check mesh processor
        try:
            mesh_health = await mesh_processor.health_check()
            health_data["components"]["mesh_processor"] = mesh_health
        except Exception as e:
            health_data["components"]["mesh_processor"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Check rendering manager
        try:
            manager_health = await rendering_manager.health_check()
            health_data["components"]["rendering_manager"] = manager_health
        except Exception as e:
            health_data["components"]["rendering_manager"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Determine overall status
        component_statuses = [
            comp.get("status", "unknown") 
            for comp in health_data["components"].values()
        ]
        
        if all(status == "healthy" for status in component_statuses):
            health_data["status"] = "healthy"
        elif any(status == "error" for status in component_statuses):
            health_data["status"] = "error"
        else:
            health_data["status"] = "degraded"
        
        return health_data
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/readiness")
async def readiness_check(
    nerf_service=Depends(get_nerf_service)
) -> Dict[str, Any]:
    """Readiness check for Kubernetes deployment."""
    try:
        # Check if core services are ready
        rendering_queue = await get_rendering_queue()
        redis_ready = await rendering_queue.health_check()
        
        # Check if NeRF service is ready
        nerf_health = await nerf_service.health_check()
        nerf_ready = nerf_health.get("status") == "healthy"
        
        ready = redis_ready and nerf_ready
        
        return {
            "ready": ready,
            "checks": {
                "redis_queue": redis_ready,
                "nerf_service": nerf_ready
            }
        }
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "ready": False,
            "error": str(e)
        }


@router.get("/liveness")
async def liveness_check() -> Dict[str, Any]:
    """Liveness check for Kubernetes deployment."""
    return {
        "alive": True,
        "service": "NeRF Rendering Service"
    }