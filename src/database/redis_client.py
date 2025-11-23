import os
import json
import logging
import redis
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class RedisClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
            cls._instance.client = None
            cls._instance.connect()
        return cls._instance
    
    def connect(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            self.client = redis.from_url(redis_url, decode_responses=True)
            self.client.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis, falling back to memory (not persistent): {e}")
            self.client = None

    def get_list(self, key: str, start: int = 0, end: int = -1) -> List[Dict[str, Any]]:
        """Get items from a Redis list, assuming JSON stored."""
        if not self.client:
            return []
        try:
            items = self.client.lrange(key, start, end)
            return [json.loads(i) for i in items]
        except Exception as e:
            logger.error(f"Redis read error for {key}: {e}")
            return []
            
    def push_to_list(self, key: str, item: Dict[str, Any], max_len: int = 1000, ttl: int = 3600):
        """Push item to list with cap and TTL."""
        if not self.client:
            return
        try:
            value = json.dumps(item)
            pipe = self.client.pipeline()
            pipe.rpush(key, value)
            pipe.ltrim(key, -max_len, -1) # Keep last N items
            pipe.expire(key, ttl)
            pipe.execute()
        except Exception as e:
            logger.error(f"Redis write error for {key}: {e}")

    def get(self, key: str) -> Optional[str]:
        if not self.client: return None
        return self.client.get(key)
        
    def set(self, key: str, value: str, ttl: Optional[int] = None):
        if not self.client: return
        self.client.set(key, value, ex=ttl)

redis_client = RedisClient()
