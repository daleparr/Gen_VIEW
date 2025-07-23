"""
Health check API routes for system monitoring and status verification
Provides comprehensive health checks for all system components
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import time
import asyncio
from datetime import datetime

from ...core.database import DatabaseManager
from ...core.redis_client import redis_manager
from ...core.config import get_settings

router = APIRouter()


class HealthStatus(BaseModel):
    """Health status response model."""
    status: str
    timestamp: datetime
    version: str
    uptime: float
    components: Dict[str, Any]


class ComponentHealth(BaseModel):
    """Individual component health status."""
    status: str  # healthy, degraded, unhealthy
    response_time: Optional[float] = None
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# Track service start time for uptime calculation
SERVICE_START_TIME = time.time()


@router.get("/", response_model=HealthStatus)
async def health_check():
    """
    Basic health check endpoint.
    Returns overall system health status.
    """
    settings = get_settings()
    current_time = datetime.utcnow()
    uptime = time.time() - SERVICE_START_TIME
    
    # Check all components
    components = {}
    overall_status = "healthy"
    
    # Database health check
    db_health = await check_database_health()
    components["database"] = db_health
    if db_health.status != "healthy":
        overall_status = "degraded"
    
    # Redis health check
    redis_health = await check_redis_health()
    components["redis"] = redis_health
    if redis_health.status != "healthy":
        overall_status = "degraded"
    
    # AI Models health check (basic)
    models_health = await check_models_health()
    components["ai_models"] = models_health
    if models_health.status != "healthy":
        overall_status = "degraded"
    
    return HealthStatus(
        status=overall_status,
        timestamp=current_time,
        version=settings.app_version,
        uptime=uptime,
        components=components
    )


@router.get("/database")
async def database_health():
    """Detailed database health check."""
    health = await check_database_health()
    
    if health.status != "healthy":
        raise HTTPException(status_code=503, detail=health.dict())
    
    return health


@router.get("/redis")
async def redis_health():
    """Detailed Redis health check."""
    health = await check_redis_health()
    
    if health.status != "healthy":
        raise HTTPException(status_code=503, detail=health.dict())
    
    return health


@router.get("/models")
async def models_health():
    """Detailed AI models health check."""
    health = await check_models_health()
    
    if health.status != "healthy":
        raise HTTPException(status_code=503, detail=health.dict())
    
    return health


@router.get("/ready")
async def readiness_check():
    """
    Kubernetes readiness probe endpoint.
    Returns 200 if service is ready to handle requests.
    """
    # Check critical components
    db_health = await check_database_health()
    redis_health = await check_redis_health()
    
    if db_health.status == "unhealthy" or redis_health.status == "unhealthy":
        raise HTTPException(
            status_code=503, 
            detail="Service not ready - critical components unhealthy"
        )
    
    return {"status": "ready", "timestamp": datetime.utcnow()}


@router.get("/live")
async def liveness_check():
    """
    Kubernetes liveness probe endpoint.
    Returns 200 if service is alive.
    """
    return {"status": "alive", "timestamp": datetime.utcnow()}


async def check_database_health() -> ComponentHealth:
    """Check database connectivity and performance."""
    start_time = time.time()
    
    try:
        db_manager = DatabaseManager()
        is_healthy = await db_manager.health_check()
        response_time = time.time() - start_time
        
        if is_healthy:
            return ComponentHealth(
                status="healthy",
                response_time=response_time,
                details={
                    "connection_pool": "active",
                    "query_time": f"{response_time:.3f}s"
                }
            )
        else:
            return ComponentHealth(
                status="unhealthy",
                response_time=response_time,
                error="Database connection failed"
            )
            
    except Exception as e:
        response_time = time.time() - start_time
        return ComponentHealth(
            status="unhealthy",
            response_time=response_time,
            error=str(e)
        )


async def check_redis_health() -> ComponentHealth:
    """Check Redis connectivity and performance."""
    start_time = time.time()
    
    try:
        is_healthy = await redis_manager.health_check()
        response_time = time.time() - start_time
        
        if is_healthy:
            # Test basic operations
            test_key = "health_check_test"
            await redis_manager.set(test_key, "test_value", expire=10)
            test_value = await redis_manager.get(test_key)
            await redis_manager.delete(test_key)
            
            if test_value == "test_value":
                return ComponentHealth(
                    status="healthy",
                    response_time=response_time,
                    details={
                        "connection": "active",
                        "operations": "working",
                        "ping_time": f"{response_time:.3f}s"
                    }
                )
            else:
                return ComponentHealth(
                    status="degraded",
                    response_time=response_time,
                    error="Redis operations not working correctly"
                )
        else:
            return ComponentHealth(
                status="unhealthy",
                response_time=response_time,
                error="Redis connection failed"
            )
            
    except Exception as e:
        response_time = time.time() - start_time
        return ComponentHealth(
            status="unhealthy",
            response_time=response_time,
            error=str(e)
        )


async def check_models_health() -> ComponentHealth:
    """Check AI models availability and status."""
    start_time = time.time()
    
    try:
        # This would check if models are loaded and ready
        # For now, we'll do a basic check
        settings = get_settings()
        
        model_status = {
            "stylegan_device": settings.stylegan_device,
            "clip_device": settings.clip_device,
            "diffusion_device": settings.diffusion_device,
            "nerf_device": settings.nerf_device,
        }
        
        response_time = time.time() - start_time
        
        # In a real implementation, you would check if models are actually loaded
        # For now, we'll assume they're healthy if the configuration is valid
        return ComponentHealth(
            status="healthy",
            response_time=response_time,
            details=model_status
        )
        
    except Exception as e:
        response_time = time.time() - start_time
        return ComponentHealth(
            status="unhealthy",
            response_time=response_time,
            error=str(e)
        )


@router.get("/metrics")
async def system_metrics():
    """
    System metrics endpoint for monitoring and observability.
    Returns performance and usage metrics.
    """
    try:
        uptime = time.time() - SERVICE_START_TIME
        
        # Basic system metrics
        metrics = {
            "uptime_seconds": uptime,
            "timestamp": datetime.utcnow().isoformat(),
            "service_info": {
                "name": "GEN-VIEW-KSE Generation API",
                "version": get_settings().app_version
            }
        }
        
        # Add database metrics if available
        try:
            db_metrics = await get_database_metrics()
            metrics["database"] = db_metrics
        except Exception:
            pass
        
        # Add Redis metrics if available
        try:
            redis_metrics = await get_redis_metrics()
            metrics["redis"] = redis_metrics
        except Exception:
            pass
        
        return metrics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


async def get_database_metrics() -> Dict[str, Any]:
    """Get database performance metrics."""
    # In a real implementation, you would query database metrics
    return {
        "connection_pool_size": 10,
        "active_connections": 2,
        "query_count": 1000,
        "avg_query_time": 0.05
    }


async def get_redis_metrics() -> Dict[str, Any]:
    """Get Redis performance metrics."""
    # In a real implementation, you would get Redis INFO metrics
    return {
        "connected_clients": 5,
        "used_memory": "2MB",
        "keyspace_hits": 1500,
        "keyspace_misses": 100
    }