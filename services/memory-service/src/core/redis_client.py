"""
Redis client configuration and connection management for KSE Memory Service
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


class RedisManager:
    """Redis operations manager with caching utilities."""
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self.settings = get_settings()
    
    async def initialize(self):
        """Initialize Redis client."""
        self.client = await get_redis_client()
    
    async def set(
        self,
        key: str,
        value: Union[str, Dict, List],
        ttl: Optional[int] = None
    ) -> bool:
        """Set a value in Redis with optional TTL."""
        if self.client is None:
            raise RuntimeError("Redis client not initialized")
        
        # Serialize complex objects to JSON
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        ttl = ttl or self.settings.cache_ttl
        return await self.client.setex(key, ttl, value)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from Redis."""
        if self.client is None:
            raise RuntimeError("Redis client not initialized")
        
        value = await self.client.get(key)
        if value is None:
            return None
        
        # Try to deserialize JSON
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value.decode('utf-8') if isinstance(value, bytes) else value
    
    async def delete(self, key: str) -> bool:
        """Delete a key from Redis."""
        if self.client is None:
            raise RuntimeError("Redis client not initialized")
        
        return bool(await self.client.delete(key))
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists in Redis."""
        if self.client is None:
            raise RuntimeError("Redis client not initialized")
        
        return bool(await self.client.exists(key))
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL for a key."""
        if self.client is None:
            raise RuntimeError("Redis client not initialized")
        
        return bool(await self.client.expire(key, ttl))
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment a numeric value."""
        if self.client is None:
            raise RuntimeError("Redis client not initialized")
        
        return await self.client.incrby(key, amount)
    
    async def set_hash(self, key: str, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set a hash in Redis."""
        if self.client is None:
            raise RuntimeError("Redis client not initialized")
        
        # Serialize values
        serialized_mapping = {}
        for k, v in mapping.items():
            if isinstance(v, (dict, list)):
                serialized_mapping[k] = json.dumps(v)
            else:
                serialized_mapping[k] = str(v)
        
        await self.client.hset(key, mapping=serialized_mapping)
        
        if ttl:
            await self.client.expire(key, ttl)
        
        return True
    
    async def get_hash(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a hash from Redis."""
        if self.client is None:
            raise RuntimeError("Redis client not initialized")
        
        hash_data = await self.client.hgetall(key)
        if not hash_data:
            return None
        
        # Deserialize values
        result = {}
        for k, v in hash_data.items():
            k = k.decode('utf-8') if isinstance(k, bytes) else k
            v = v.decode('utf-8') if isinstance(v, bytes) else v
            
            try:
                result[k] = json.loads(v)
            except (json.JSONDecodeError, TypeError):
                result[k] = v
        
        return result
    
    async def add_to_set(self, key: str, *values: str) -> int:
        """Add values to a set."""
        if self.client is None:
            raise RuntimeError("Redis client not initialized")
        
        return await self.client.sadd(key, *values)
    
    async def get_set(self, key: str) -> List[str]:
        """Get all members of a set."""
        if self.client is None:
            raise RuntimeError("Redis client not initialized")
        
        members = await self.client.smembers(key)
        return [m.decode('utf-8') if isinstance(m, bytes) else m for m in members]
    
    async def remove_from_set(self, key: str, *values: str) -> int:
        """Remove values from a set."""
        if self.client is None:
            raise RuntimeError("Redis client not initialized")
        
        return await self.client.srem(key, *values)
    
    async def publish(self, channel: str, message: Union[str, Dict]) -> int:
        """Publish a message to a channel."""
        if self.client is None:
            raise RuntimeError("Redis client not initialized")
        
        if isinstance(message, dict):
            message = json.dumps(message)
        
        return await self.client.publish(channel, message)
    
    async def flush_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        if self.client is None:
            raise RuntimeError("Redis client not initialized")
        
        keys = await self.client.keys(pattern)
        if keys:
            return await self.client.delete(*keys)
        return 0
    
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


# Global Redis manager instance
redis_manager: Optional[RedisManager] = None


async def get_redis_manager() -> RedisManager:
    """Get Redis manager instance."""
    global redis_manager
    if redis_manager is None:
        redis_manager = RedisManager()
        await redis_manager.initialize()
    return redis_manager