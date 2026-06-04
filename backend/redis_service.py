"""
redis_service.py — Upstash Redis service helper
Handles caching, distributed locking, and live log sharing across scaled instances.
"""
import json
import redis
from contextlib import contextmanager
from typing import List, Optional
from config import settings

class RedisService:
    def __init__(self):
        self._client: Optional[redis.Redis] = None

    @property
    def client(self) -> redis.Redis:
        """Lazy loader for Redis client"""
        if self._client is None:
            self._client = redis.Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=5,
                retry_on_timeout=True
            )
        return self._client

    def is_connected(self) -> bool:
        """Test connection to Redis"""
        try:
            return bool(self.client.ping())
        except Exception as e:
            print(f"[Redis] Connection test failed: {e}")
            return False

    # ── Log Streaming ─────────────────────────────────────────────────────────

    def push_log(self, message: str, max_logs: int = 200):
        """Append log message to a Redis list and cap the size"""
        try:
            self.client.rpush("list:pipeline_logs", message)
            self.client.ltrim("list:pipeline_logs", -max_logs, -1)
        except Exception as e:
            print(f"[Redis] Failed to push log: {e}")

    def get_logs(self, limit: int = 100) -> List[str]:
        """Fetch latest log messages from Redis"""
        try:
            return self.client.lrange("list:pipeline_logs", -limit, -1)
        except Exception as e:
            print(f"[Redis] Failed to fetch logs: {e}")
            return []

    # ── News Caching ──────────────────────────────────────────────────────────

    def cache_news(self, articles: List[dict], expire_seconds: int = 3600):
        """Cache researched top news"""
        try:
            self.client.set("cache:latest_news", json.dumps(articles), ex=expire_seconds)
        except Exception as e:
            print(f"[Redis] Failed to cache news: {e}")

    def get_cached_news(self) -> Optional[List[dict]]:
        """Retrieve cached news if available"""
        try:
            raw = self.client.get("cache:latest_news")
            if raw:
                return json.loads(raw)
        except Exception as e:
            print(f"[Redis] Failed to fetch cached news: {e}")
        return None

    # ── Distributed Lock ──────────────────────────────────────────────────────

    @contextmanager
    def acquire_lock(self, lock_name: str, expire_seconds: int = 600):
        """
        Distributed lock context manager using Redis SETNX (set if not exists).
        Yields True if lock is successfully acquired, False otherwise.
        """
        lock_key = f"lock:{lock_name}"
        acquired = False
        try:
            # Try to acquire lock. NX=True sets key only if it does not exist
            acquired = bool(self.client.set(lock_key, "active", nx=True, ex=expire_seconds))
            yield acquired
        except Exception as e:
            print(f"[Redis] Lock exception ({lock_name}): {e}")
            yield False
        finally:
            if acquired:
                try:
                    self.client.delete(lock_key)
                except Exception as e:
                    print(f"[Redis] Failed to release lock ({lock_name}): {e}")


# Singleton instance
redis_service = RedisService()
