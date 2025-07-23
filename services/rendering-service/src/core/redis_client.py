"""
Redis client configuration for NeRF Rendering Service
Handles task queues and caching for rendering operations
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
import redis.asyncio as redis
from redis.asyncio import ConnectionPool

from .config import get_settings

logger = logging.getLogger(__name__)

# Global Redis client
redis_client: Optional[redis.Redis] = None
redis_pool: Optional[ConnectionPool] = None


async def init_redis() -> None:
    """Initialize Redis connection."""
    global redis_client, redis_pool
    
    settings = get_settings()
    
    # Create connection pool
    redis_pool = ConnectionPool.from_url(
        settings.redis_url,
        max_connections=settings.redis_max_connections,
        socket_timeout=settings.redis_socket_timeout,
        socket_connect_timeout=settings.redis_socket_timeout,
        retry_on_timeout=True,
        health_check_interval=30
    )
    
    # Create Redis client
    redis_client = redis.Redis(connection_pool=redis_pool)
    
    # Test connection
    try:
        await redis_client.ping()
        logger.info("Redis connection established successfully")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise


async def close_redis() -> None:
    """Close Redis connections."""
    global redis_client, redis_pool
    
    if redis_client:
        await redis_client.close()
        logger.info("Redis client closed")
    
    if redis_pool:
        await redis_pool.disconnect()
        logger.info("Redis connection pool closed")


async def get_redis_client() -> redis.Redis:
    """Get Redis client instance."""
    if redis_client is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    return redis_client


class RenderingQueue:
    """Redis-based rendering task queue manager."""
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self.settings = get_settings()
        
        # Queue names
        self.render_queue = "rendering:queue"
        self.nerf_queue = "nerf:queue"
        self.mesh_queue = "mesh:queue"
        self.priority_queue = "rendering:priority"
        
        # Status tracking
        self.active_jobs = "rendering:active"
        self.completed_jobs = "rendering:completed"
        self.failed_jobs = "rendering:failed"
    
    async def initialize(self):
        """Initialize Redis client."""
        self.client = await get_redis_client()
    
    async def add_render_job(
        self,
        job_id: str,
        job_data: Dict[str, Any],
        priority: int = 0,
        queue_name: Optional[str] = None
    ) -> bool:
        """Add a rendering job to the queue."""
        if self.client is None:
            raise RuntimeError("Redis client not initialized")
        
        try:
            # Serialize job data
            job_payload = {
                "job_id": job_id,
                "data": job_data,
                "created_at": asyncio.get_event_loop().time(),
                "priority": priority
            }
            
            serialized_job = json.dumps(job_payload)
            
            # Choose queue based on priority or type
            if priority > 0:
                queue = self.priority_queue
            else:
                queue = queue_name or self.render_queue
            
            # Add to queue (FIFO for normal, sorted set for priority)
            if priority > 0:
                await self.client.zadd(queue, {serialized_job: priority})
            else:
                await self.client.lpush(queue, serialized_job)
            
            # Track active job
            await self.client.hset(self.active_jobs, job_id, serialized_job)
            
            logger.info(f"Added rendering job {job_id} to queue {queue}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add render job {job_id}: {e}")
            return False
    
    async def get_next_job(self, timeout: int = 10) -> Optional[Dict[str, Any]]:
        """Get the next job from the queue."""
        if self.client is None:
            raise RuntimeError("Redis client not initialized")
        
        try:
            # Check priority queue first
            priority_job = await self.client.zpopmax(self.priority_queue)
            if priority_job:
                job_data = json.loads(priority_job[0][0])
                return job_data
            
            # Then check regular queues
            queues = [self.render_queue, self.nerf_queue, self.mesh_queue]
            
            # Use BRPOP for blocking pop with timeout
            result = await self.client.brpop(queues, timeout=timeout)
            if result:
                queue_name, job_data = result
                return json.loads(job_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get next job: {e}")
            return None
    
    async def mark_job_completed(self, job_id: str, result_data: Dict[str, Any]) -> bool:
        """Mark a job as completed."""
        if self.client is None:
            raise RuntimeError("Redis client not initialized")
        
        try:
            # Move from active to completed
            job_data = await self.client.hget(self.active_jobs, job_id)
            if job_data:
                # Add completion data
                completed_job = {
                    "job_id": job_id,
                    "original_data": json.loads(job_data),
                    "result": result_data,
                    "completed_at": asyncio.get_event_loop().time()
                }
                
                await self.client.hset(
                    self.completed_jobs, 
                    job_id, 
                    json.dumps(completed_job)
                )
                await self.client.hdel(self.active_jobs, job_id)
                
                # Set expiration for completed jobs (24 hours)
                await self.client.expire(f"{self.completed_jobs}:{job_id}", 86400)
                
                logger.info(f"Marked job {job_id} as completed")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to mark job {job_id} as completed: {e}")
            return False
    
    async def mark_job_failed(self, job_id: str, error_message: str) -> bool:
        """Mark a job as failed."""
        if self.client is None:
            raise RuntimeError("Redis client not initialized")
        
        try:
            # Move from active to failed
            job_data = await self.client.hget(self.active_jobs, job_id)
            if job_data:
                failed_job = {
                    "job_id": job_id,
                    "original_data": json.loads(job_data),
                    "error": error_message,
                    "failed_at": asyncio.get_event_loop().time()
                }
                
                await self.client.hset(
                    self.failed_jobs, 
                    job_id, 
                    json.dumps(failed_job)
                )
                await self.client.hdel(self.active_jobs, job_id)
                
                logger.error(f"Marked job {job_id} as failed: {error_message}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to mark job {job_id} as failed: {e}")
            return False
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a job."""
        if self.client is None:
            raise RuntimeError("Redis client not initialized")
        
        try:
            # Check active jobs
            active_job = await self.client.hget(self.active_jobs, job_id)
            if active_job:
                return {
                    "status": "active",
                    "data": json.loads(active_job)
                }
            
            # Check completed jobs
            completed_job = await self.client.hget(self.completed_jobs, job_id)
            if completed_job:
                return {
                    "status": "completed",
                    "data": json.loads(completed_job)
                }
            
            # Check failed jobs
            failed_job = await self.client.hget(self.failed_jobs, job_id)
            if failed_job:
                return {
                    "status": "failed",
                    "data": json.loads(failed_job)
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get job status for {job_id}: {e}")
            return None
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get statistics about the queues."""
        if self.client is None:
            raise RuntimeError("Redis client not initialized")
        
        try:
            stats = {
                "render_queue_size": await self.client.llen(self.render_queue),
                "nerf_queue_size": await self.client.llen(self.nerf_queue),
                "mesh_queue_size": await self.client.llen(self.mesh_queue),
                "priority_queue_size": await self.client.zcard(self.priority_queue),
                "active_jobs": await self.client.hlen(self.active_jobs),
                "completed_jobs": await self.client.hlen(self.completed_jobs),
                "failed_jobs": await self.client.hlen(self.failed_jobs)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            return {}
    
    async def health_check(self) -> bool:
        """Check Redis connectivity."""
        try:
            if self.client is None:
                return False
            
            await self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False


# Global rendering queue instance
rendering_queue: Optional[RenderingQueue] = None


async def get_rendering_queue() -> RenderingQueue:
    """Get rendering queue instance."""
    global rendering_queue
    if rendering_queue is None:
        rendering_queue = RenderingQueue()
        await rendering_queue.initialize()
    return rendering_queue