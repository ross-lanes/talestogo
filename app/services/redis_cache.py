"""
Redis caching service for analytics data.

This service provides a caching layer for expensive analytics calculations,
significantly reducing database load and improving response times for
frequently accessed dashboard and analytics data.

Cache TTL Strategy:
- Dashboard data: 15 minutes (frequent updates needed)
- Trends data: 1 hour (less frequently changing)
- Batch analytics: 24 hours (static once computed)
"""

import json
import redis
import logging
from typing import Any, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Redis-based caching service for analytics data.

    Provides methods to cache and retrieve analytics results with automatic
    expiration and invalidation support.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """
        Initialize Redis cache connection.

        Args:
            redis_url: Redis connection URL (default: localhost)
        """
        try:
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            self.is_available = True
            logger.info("Redis cache connected successfully")
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(f"Redis cache unavailable: {e}. Operating without cache.")
            self.redis_client = None
            self.is_available = False

    def _make_key(self, prefix: str, user_id: int, brand_id: Optional[int] = None,
                  batch_id: Optional[int] = None, **kwargs) -> str:
        """
        Generate cache key with consistent format.

        Args:
            prefix: Cache key prefix (e.g., 'dashboard', 'trends')
            user_id: User ID for multi-tenancy
            brand_id: Optional brand ID
            batch_id: Optional batch ID
            **kwargs: Additional key components

        Returns:
            Formatted cache key string
        """
        parts = [prefix, str(user_id)]

        if brand_id is not None:
            parts.append(f"brand:{brand_id}")
        if batch_id is not None:
            parts.append(f"batch:{batch_id}")

        # Add any additional kwargs
        for key, value in sorted(kwargs.items()):
            if value is not None:
                parts.append(f"{key}:{value}")

        return ":".join(parts)

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached data by key.

        Args:
            key: Cache key

        Returns:
            Cached data as dictionary, or None if not found/cache unavailable
        """
        if not self.is_available:
            return None

        try:
            cached = self.redis_client.get(key)
            if cached:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(cached)
            else:
                logger.debug(f"Cache MISS: {key}")
                return None
        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.error(f"Error retrieving from cache: {e}")
            return None

    def set(self, key: str, data: Dict[str, Any], ttl_seconds: int = 900) -> bool:
        """
        Store data in cache with TTL.

        Args:
            key: Cache key
            data: Data to cache (must be JSON-serializable)
            ttl_seconds: Time to live in seconds (default: 15 minutes)

        Returns:
            True if successful, False otherwise
        """
        if not self.is_available:
            return False

        try:
            serialized = json.dumps(data, default=str)  # default=str handles datetime objects
            self.redis_client.setex(key, ttl_seconds, serialized)
            logger.debug(f"Cache SET: {key} (TTL: {ttl_seconds}s)")
            return True
        except (redis.RedisError, TypeError) as e:
            logger.error(f"Error storing to cache: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete specific cache key.

        Args:
            key: Cache key to delete

        Returns:
            True if successful, False otherwise
        """
        if not self.is_available:
            return False

        try:
            self.redis_client.delete(key)
            logger.debug(f"Cache DELETE: {key}")
            return True
        except redis.RedisError as e:
            logger.error(f"Error deleting from cache: {e}")
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching a pattern.

        Args:
            pattern: Redis key pattern (e.g., 'dashboard:123:*')

        Returns:
            Number of keys deleted
        """
        if not self.is_available:
            return 0

        try:
            count = 0
            for key in self.redis_client.scan_iter(match=pattern):
                self.redis_client.delete(key)
                count += 1
            logger.info(f"Cache INVALIDATE: {pattern} ({count} keys)")
            return count
        except redis.RedisError as e:
            logger.error(f"Error invalidating cache pattern: {e}")
            return 0

    def invalidate_user(self, user_id: int, brand_id: Optional[int] = None) -> int:
        """
        Invalidate all cache entries for a user/brand.

        Args:
            user_id: User ID
            brand_id: Optional brand ID (if None, invalidates all brands for user)

        Returns:
            Number of keys deleted
        """
        if brand_id is not None:
            pattern = f"*:{user_id}:brand:{brand_id}:*"
        else:
            pattern = f"*:{user_id}:*"

        return self.invalidate_pattern(pattern)

    def invalidate_batch(self, user_id: int, brand_id: int, batch_id: int) -> int:
        """
        Invalidate all cache entries for a specific batch.

        Args:
            user_id: User ID
            brand_id: Brand ID
            batch_id: Batch ID

        Returns:
            Number of keys deleted
        """
        pattern = f"*:{user_id}:brand:{brand_id}:batch:{batch_id}*"
        return self.invalidate_pattern(pattern)

    # High-level cache methods for specific data types

    def get_dashboard_data(self, user_id: int, brand_id: int,
                          batch_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get cached dashboard data.

        Args:
            user_id: User ID
            brand_id: Brand ID
            batch_id: Optional batch filter

        Returns:
            Cached dashboard data or None
        """
        key = self._make_key("dashboard", user_id, brand_id, batch_id)
        return self.get(key)

    def set_dashboard_data(self, user_id: int, brand_id: int, data: Dict[str, Any],
                          batch_id: Optional[int] = None, ttl_seconds: int = 900) -> bool:
        """
        Cache dashboard data.

        Args:
            user_id: User ID
            brand_id: Brand ID
            data: Dashboard data to cache
            batch_id: Optional batch filter
            ttl_seconds: Cache TTL (default: 15 minutes)

        Returns:
            True if successful
        """
        key = self._make_key("dashboard", user_id, brand_id, batch_id)
        return self.set(key, data, ttl_seconds)

    def get_sentiment_breakdown(self, user_id: int, brand_id: int,
                               batch_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get cached sentiment breakdown data."""
        key = self._make_key("sentiment", user_id, brand_id, batch_id)
        return self.get(key)

    def set_sentiment_breakdown(self, user_id: int, brand_id: int, data: Dict[str, Any],
                               batch_id: Optional[int] = None, ttl_seconds: int = 900) -> bool:
        """Cache sentiment breakdown data."""
        key = self._make_key("sentiment", user_id, brand_id, batch_id)
        return self.set(key, data, ttl_seconds)

    def get_positioning_breakdown(self, user_id: int, brand_id: int,
                                 batch_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get cached positioning breakdown data."""
        key = self._make_key("positioning", user_id, brand_id, batch_id)
        return self.get(key)

    def set_positioning_breakdown(self, user_id: int, brand_id: int, data: Dict[str, Any],
                                 batch_id: Optional[int] = None, ttl_seconds: int = 900) -> bool:
        """Cache positioning breakdown data."""
        key = self._make_key("positioning", user_id, brand_id, batch_id)
        return self.set(key, data, ttl_seconds)

    def get_share_of_voice(self, user_id: int, brand_id: int,
                          batch_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get cached share of voice data."""
        key = self._make_key("sov", user_id, brand_id, batch_id)
        return self.get(key)

    def set_share_of_voice(self, user_id: int, brand_id: int, data: Dict[str, Any],
                          batch_id: Optional[int] = None, ttl_seconds: int = 900) -> bool:
        """Cache share of voice data."""
        key = self._make_key("sov", user_id, brand_id, batch_id)
        return self.set(key, data, ttl_seconds)

    def get_trends(self, user_id: int, brand_id: int, grouping: str = "week") -> Optional[Dict[str, Any]]:
        """Get cached trend data."""
        key = self._make_key("trends", user_id, brand_id, grouping=grouping)
        return self.get(key)

    def set_trends(self, user_id: int, brand_id: int, data: Dict[str, Any],
                   grouping: str = "week", ttl_seconds: int = 3600) -> bool:
        """Cache trend data (longer TTL since trends change less frequently)."""
        key = self._make_key("trends", user_id, brand_id, grouping=grouping)
        return self.set(key, data, ttl_seconds)


# Global cache instance (initialized in main.py)
_cache_instance: Optional[RedisCache] = None


def get_redis_cache() -> RedisCache:
    """
    Get the global Redis cache instance.

    Returns:
        RedisCache instance
    """
    global _cache_instance
    if _cache_instance is None:
        import os
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _cache_instance = RedisCache(redis_url)
    return _cache_instance


def invalidate_analytics_cache(user_id: int, brand_id: Optional[int] = None):
    """
    Invalidate all analytics cache for a user/brand.

    Use this when data changes (new responses, edits, deletions).

    Args:
        user_id: User ID
        brand_id: Optional brand ID
    """
    cache = get_redis_cache()
    count = cache.invalidate_user(user_id, brand_id)
    logger.info(f"Invalidated {count} cache entries for user {user_id}, brand {brand_id}")
