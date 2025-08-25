"""
Redis service for OpsFlow Guardian 2.0
Handles caching, session management, and real-time data
"""

import redis.asyncio as redis
import json
import logging
from typing import Any, Optional, Dict, List
from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisService:
    """Redis service for caching and real-time data management"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.cache_client: Optional[redis.Redis] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Redis connections"""
        if self._initialized:
            return
        
        try:
            # Check if Redis URL is available
            if not settings.REDIS_URL:
                logger.warning("Redis not configured - running without cache")
                self._initialized = True
                return
                
            # Main Redis connection
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={},
            )
            
            # Cache Redis connection (use same URL if not specified)
            cache_url = getattr(settings, 'REDIS_CACHE_URL', None) or settings.REDIS_URL
            self.cache_client = redis.from_url(
                cache_url,
                encoding="utf-8",
                decode_responses=True,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={},
            )
            
            # Test connections
            await self.redis_client.ping()
            await self.cache_client.ping()
            
            self._initialized = True
            logger.info("Redis service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis service: {e}")
            raise
    
    async def close(self):
        """Close Redis connections"""
        try:
            if self.redis_client:
                await self.redis_client.close()
            if self.cache_client:
                await self.cache_client.close()
            logger.info("Redis connections closed")
        except Exception as e:
            logger.error(f"Error closing Redis connections: {e}")
    
    async def ping(self) -> bool:
        """Test Redis connectivity"""
        try:
            if not self.redis_client:
                return False
            await self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False
    
    # Basic operations
    async def set(self, key: str, value: str, expire: Optional[int] = None) -> bool:
        """Set a key-value pair"""
        try:
            if expire:
                await self.redis_client.setex(key, expire, value)
            else:
                await self.redis_client.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Failed to set key {key}: {e}")
            return False
    
    async def get(self, key: str) -> Optional[str]:
        """Get a value by key"""
        try:
            return await self.redis_client.get(key)
        except Exception as e:
            logger.error(f"Failed to get key {key}: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete a key"""
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return bool(await self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Failed to check existence of key {key}: {e}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for a key"""
        try:
            await self.redis_client.expire(key, seconds)
            return True
        except Exception as e:
            logger.error(f"Failed to set expiration for key {key}: {e}")
            return False
    
    # JSON operations
    async def set_json(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set a JSON value"""
        try:
            json_value = json.dumps(value, default=str)
            return await self.set(key, json_value, expire)
        except Exception as e:
            logger.error(f"Failed to set JSON key {key}: {e}")
            return False
    
    async def get_json(self, key: str) -> Optional[Any]:
        """Get a JSON value"""
        try:
            value = await self.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Failed to get JSON key {key}: {e}")
            return None
    
    # List operations
    async def list_push(self, key: str, *values: str) -> int:
        """Push values to the left of a list"""
        try:
            return await self.redis_client.lpush(key, *values)
        except Exception as e:
            logger.error(f"Failed to push to list {key}: {e}")
            return 0
    
    async def list_pop(self, key: str) -> Optional[str]:
        """Pop value from the left of a list"""
        try:
            return await self.redis_client.lpop(key)
        except Exception as e:
            logger.error(f"Failed to pop from list {key}: {e}")
            return None
    
    async def list_get_all(self, key: str) -> List[str]:
        """Get all values from a list"""
        try:
            return await self.redis_client.lrange(key, 0, -1)
        except Exception as e:
            logger.error(f"Failed to get list {key}: {e}")
            return []
    
    async def list_length(self, key: str) -> int:
        """Get length of a list"""
        try:
            return await self.redis_client.llen(key)
        except Exception as e:
            logger.error(f"Failed to get length of list {key}: {e}")
            return 0
    
    # Hash operations
    async def hash_set(self, key: str, field: str, value: str) -> bool:
        """Set a field in a hash"""
        try:
            await self.redis_client.hset(key, field, value)
            return True
        except Exception as e:
            logger.error(f"Failed to set hash field {key}.{field}: {e}")
            return False
    
    async def hash_get(self, key: str, field: str) -> Optional[str]:
        """Get a field from a hash"""
        try:
            return await self.redis_client.hget(key, field)
        except Exception as e:
            logger.error(f"Failed to get hash field {key}.{field}: {e}")
            return None
    
    async def hash_get_all(self, key: str) -> Dict[str, str]:
        """Get all fields from a hash"""
        try:
            return await self.redis_client.hgetall(key)
        except Exception as e:
            logger.error(f"Failed to get hash {key}: {e}")
            return {}
    
    async def hash_delete(self, key: str, field: str) -> bool:
        """Delete a field from a hash"""
        try:
            await self.redis_client.hdel(key, field)
            return True
        except Exception as e:
            logger.error(f"Failed to delete hash field {key}.{field}: {e}")
            return False
    
    # Set operations
    async def set_add(self, key: str, *values: str) -> int:
        """Add values to a set"""
        try:
            return await self.redis_client.sadd(key, *values)
        except Exception as e:
            logger.error(f"Failed to add to set {key}: {e}")
            return 0
    
    async def set_remove(self, key: str, *values: str) -> int:
        """Remove values from a set"""
        try:
            return await self.redis_client.srem(key, *values)
        except Exception as e:
            logger.error(f"Failed to remove from set {key}: {e}")
            return 0
    
    async def set_members(self, key: str) -> List[str]:
        """Get all members of a set"""
        try:
            members = await self.redis_client.smembers(key)
            return list(members)
        except Exception as e:
            logger.error(f"Failed to get set members {key}: {e}")
            return []
    
    async def set_is_member(self, key: str, value: str) -> bool:
        """Check if value is a member of a set"""
        try:
            return bool(await self.redis_client.sismember(key, value))
        except Exception as e:
            logger.error(f"Failed to check set membership {key}: {e}")
            return False
    
    # Cache operations (using separate cache client)
    async def cache_set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """Set a cached value with expiration"""
        try:
            json_value = json.dumps(value, default=str)
            await self.cache_client.setex(f"cache:{key}", expire, json_value)
            return True
        except Exception as e:
            logger.error(f"Failed to cache key {key}: {e}")
            return False
    
    async def cache_get(self, key: str) -> Optional[Any]:
        """Get a cached value"""
        try:
            value = await self.cache_client.get(f"cache:{key}")
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Failed to get cached key {key}: {e}")
            return None
    
    async def cache_delete(self, key: str) -> bool:
        """Delete a cached value"""
        try:
            await self.cache_client.delete(f"cache:{key}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete cached key {key}: {e}")
            return False
    
    # Pattern operations
    async def get_keys_by_pattern(self, pattern: str) -> List[str]:
        """Get keys matching a pattern"""
        try:
            return await self.redis_client.keys(pattern)
        except Exception as e:
            logger.error(f"Failed to get keys by pattern {pattern}: {e}")
            return []
    
    async def delete_by_pattern(self, pattern: str) -> int:
        """Delete keys matching a pattern"""
        try:
            keys = await self.get_keys_by_pattern(pattern)
            if keys:
                return await self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Failed to delete keys by pattern {pattern}: {e}")
            return 0
    
    # Real-time messaging
    async def publish(self, channel: str, message: Any) -> int:
        """Publish a message to a channel"""
        try:
            json_message = json.dumps(message, default=str)
            return await self.redis_client.publish(channel, json_message)
        except Exception as e:
            logger.error(f"Failed to publish to channel {channel}: {e}")
            return 0
    
    async def subscribe(self, channel: str):
        """Subscribe to a channel"""
        try:
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe(channel)
            return pubsub
        except Exception as e:
            logger.error(f"Failed to subscribe to channel {channel}: {e}")
            return None
