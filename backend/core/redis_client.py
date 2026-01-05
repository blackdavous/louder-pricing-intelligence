"""
Redis client configuration
"""
import redis.asyncio as aioredis
from redis import Redis
from typing import Optional
import json

from core.config import settings


class RedisClient:
    """Redis client wrapper with common operations"""
    
    def __init__(self):
        self.client: Optional[Redis] = None
    
    def connect(self):
        """Create Redis connection"""
        if self.client is None:
            self.client = Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                encoding="utf-8",
            )
        return self.client
    
    def disconnect(self):
        """Close Redis connection"""
        if self.client:
            self.client.close()
            self.client = None
    
    def get(self, key: str) -> Optional[str]:
        """Get value from Redis"""
        if not self.client:
            self.connect()
        return self.client.get(key)
    
    def set(
        self,
        key: str,
        value: str,
        ex: Optional[int] = None
    ) -> bool:
        """Set value in Redis with optional expiration"""
        if not self.client:
            self.connect()
        return self.client.set(key, value, ex=ex or settings.REDIS_CACHE_TTL)
    
    def get_json(self, key: str) -> Optional[dict]:
        """Get JSON value from Redis"""
        value = self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None
    
    def set_json(
        self,
        key: str,
        value: dict,
        ex: Optional[int] = None
    ) -> bool:
        """Set JSON value in Redis"""
        json_str = json.dumps(value)
        return self.set(key, json_str, ex=ex)
    
    def delete(self, key: str) -> int:
        """Delete key from Redis"""
        if not self.client:
            self.connect()
        return self.client.delete(key)
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.client:
            self.connect()
        return self.client.exists(key) > 0


# Global Redis client instance
redis_client = RedisClient()


def get_redis() -> RedisClient:
    """Dependency to get Redis client"""
    if not redis_client.client:
        redis_client.connect()
    return redis_client
