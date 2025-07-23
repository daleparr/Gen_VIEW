"""
Redis client configuration and connection management
Used for caching and async task processing
"""

import redis.asyncio as redis
from typing import Optional, Any, Dict, List
import json
import logging
from datetime import timedelta

from .config import get_settings

logger = logging.getLogger(__name__)

# Global Redis client instance
_redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> redis.Redis:
    """Get Redis client instance with connection pooling."""
    global _redis_client
    
    if _redis_client is None:
        settings = get_settings()
        
        _redis_client = redis.from_url(
            settings.redis_url,
            max_connections=settings.redis_max_connections,
            decode_responses=True,
            retry_on_timeout=True,
            health_check_interval=30,
        )
        
        # Test connection
        try:
            await _redis_client.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    return _redis_client


async def close_redis_client():
    """Close Redis connection."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis connection closed")


class RedisManager:
    """Redis manager for caching and data operations."""
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
    
    async def initialize(self):
        """Initialize Redis client."""
        self.client = await get_redis_client()
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        expire: Optional[int] = None,
        serialize: bool = True
    ) -> bool:
        """Set a key-value pair in Redis."""
        if not self.client:
            await self.initialize()
        
        try:
            if serialize and not isinstance(value, (str, bytes)):
                value = json.dumps(value)
            
            await self.client.set(key, value, ex=expire)
            return True
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {e}")
            return False
    
    async def get(
        self, 
        key: str, 
        deserialize: bool = True,
        default: Any = None
    ) -> Any:
        """Get a value from Redis."""
        if not self.client:
            await self.initialize()
        
        try:
            value = await self.client.get(key)
            if value is None:
                return default
            
            if deserialize:
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            
            return value
        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            return default
    
    async def delete(self, key: str) -> bool:
        """Delete a key from Redis."""
        if not self.client:
            await self.initialize()
        
        try:
            result = await self.client.delete(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis DELETE error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists in Redis."""
        if not self.client:
            await self.initialize()
        
        try:
            result = await self.client.exists(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis EXISTS error for key {key}: {e}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration time for a key."""
        if not self.client:
            await self.initialize()
        
        try:
            result = await self.client.expire(key, seconds)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis EXPIRE error for key {key}: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a numeric value in Redis."""
        if not self.client:
            await self.initialize()
        
        try:
            result = await self.client.incrby(key, amount)
            return result
        except Exception as e:
            logger.error(f"Redis INCREMENT error for key {key}: {e}")
            return None
    
    async def set_hash(self, key: str, mapping: Dict[str, Any]) -> bool:
        """Set a hash in Redis."""
        if not self.client:
            await self.initialize()
        
        try:
            # Serialize complex values
            serialized_mapping = {}
            for k, v in mapping.items():
                if isinstance(v, (dict, list)):
                    serialized_mapping[k] = json.dumps(v)
                else:
                    serialized_mapping[k] = str(v)
            
            await self.client.hset(key, mapping=serialized_mapping)
            return True
        except Exception as e:
            logger.error(f"Redis HSET error for key {key}: {e}")
            return False
    
    async def get_hash(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a hash from Redis."""
        if not self.client:
            await self.initialize()
        
        try:
            result = await self.client.hgetall(key)
            if not result:
                return None
            
            # Deserialize values
            deserialized_result = {}
            for k, v in result.items():
                try:
                    deserialized_result[k] = json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    deserialized_result[k] = v
            
            return deserialized_result
        except Exception as e:
            logger.error(f"Redis HGETALL error for key {key}: {e}")
            return None
    
    async def add_to_list(self, key: str, value: Any) -> bool:
        """Add an item to a Redis list."""
        if not self.client:
            await self.initialize()
        
        try:
            if not isinstance(value, (str, bytes)):
                value = json.dumps(value)
            
            await self.client.lpush(key, value)
            return True
        except Exception as e:
            logger.error(f"Redis LPUSH error for key {key}: {e}")
            return False
    
    async def get_list(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """Get items from a Redis list."""
        if not self.client:
            await self.initialize()
        
        try:
            result = await self.client.lrange(key, start, end)
            
            # Deserialize items
            deserialized_result = []
            for item in result:
                try:
                    deserialized_result.append(json.loads(item))
                except (json.JSONDecodeError, TypeError):
                    deserialized_result.append(item)
            
            return deserialized_result
        except Exception as e:
            logger.error(f"Redis LRANGE error for key {key}: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check Redis connectivity."""
        if not self.client:
            try:
                await self.initialize()
            except Exception:
                return False
        
        try:
            await self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False


# Global Redis manager instance
redis_manager = RedisManager()