"""
Health check routes for KSE Memory Service
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import logging

from ...core.database import check_db_health
from ...core.redis_client import get_redis_manager
from ...main import get_memory_manager, get_embedding_service, get_knowledge_graph_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "service": "KSE Memory Service",
        "status": "healthy",
        "timestamp": "2025-01-23T08:00:00Z"
    }


@router.get("/detailed")
async def detailed_health_check(
    memory_manager=Depends(get_memory_manager),
    embedding_service=Depends(get_embedding_service),
    knowledge_graph_service=Depends(get_knowledge_graph_service)
) -> Dict[str, Any]:
    """Detailed health check with component status."""
    try:
        health_data = {
            "service": "KSE Memory Service",
            "status": "healthy",
            "timestamp": "2025-01-23T08:00:00Z",
            "components": {}
        }
        
        # Check database
        try:
            db_healthy = await check_db_health()
            health_data["components"]["database"] = {
                "status": "healthy" if db_healthy else "unhealthy",
                "connected": db_healthy
            }
        except Exception as e:
            health_data["components"]["database"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Check Redis
        try:
            redis_manager = await get_redis_manager()
            redis_healthy = await redis_manager.health_check()
            health_data["components"]["redis"] = {
                "status": "healthy" if redis_healthy else "unhealthy",
                "connected": redis_healthy
            }
        except Exception as e:
            health_data["components"]["redis"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Check memory manager
        try:
            memory_health = await memory_manager.health_check()
            health_data["components"]["memory_manager"] = memory_health
        except Exception as e:
            health_data["components"]["memory_manager"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Check embedding service
        try:
            embedding_health = await embedding_service.health_check()
            health_data["components"]["embedding_service"] = embedding_health
        except Exception as e:
            health_data["components"]["embedding_service"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Check knowledge graph service
        try:
            kg_health = await knowledge_graph_service.health_check()
            health_data["components"]["knowledge_graph_service"] = kg_health
        except Exception as e:
            health_data["components"]["knowledge_graph_service"] = {
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
    memory_manager=Depends(get_memory_manager),
    embedding_service=Depends(get_embedding_service)
) -> Dict[str, Any]:
    """Readiness check for Kubernetes deployment."""
    try:
        # Check if core services are ready
        db_ready = await check_db_health()
        
        redis_manager = await get_redis_manager()
        redis_ready = await redis_manager.health_check()
        
        # Check if embedding service is ready
        embedding_health = await embedding_service.health_check()
        embedding_ready = embedding_health.get("status") == "healthy"
        
        ready = db_ready and redis_ready and embedding_ready
        
        return {
            "ready": ready,
            "checks": {
                "database": db_ready,
                "redis": redis_ready,
                "embedding_service": embedding_ready
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
        "service": "KSE Memory Service"
    }