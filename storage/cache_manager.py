"""
Hybrid Caching System: In-Memory (fast) + Redis (persistent)
Automatically falls back to in-memory if Redis unavailable
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)

# Try to import Redis (optional dependency)
try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("⚠️ Redis not installed. Using in-memory cache only.")


class CacheManager:
    """Hybrid cache: L1 (memory) + L2 (Redis)"""
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        memory_ttl: int = 3600,      # 1 hour in-memory
        redis_ttl: int = 86400,       # 24 hours in Redis
        max_memory_items: int = 1000  # Max items in memory
    ):
        self.memory_cache = {}  # L1: Fast but limited
        self.memory_ttl = memory_ttl
        self.redis_ttl = redis_ttl
        self.max_memory_items = max_memory_items
        
        # Try to connect to Redis
        self.redis = None
        if REDIS_AVAILABLE and redis_url:
            try:
                self.redis = aioredis.from_url(
                    redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                logger.info("✅ Redis connected")
            except Exception as e:
                logger.warning(f"⚠️ Redis connection failed: {e}")
                logger.info("📦 Falling back to in-memory cache")
    
    
    def _make_key(self, namespace: str, key: str) -> str:
        """Generate cache key"""
        # Hash for shorter keys
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return f"scrapigen:{namespace}:{key_hash}"
    
    
    async def get(self, namespace: str, key: str) -> Optional[Any]:
        """
        Get from cache (L1 first, then L2)
        
        Args:
            namespace: Cache namespace (e.g., "rendered_html", "extracted_data")
            key: Cache key (usually URL)
        
        Returns:
            Cached value or None
        """
        
        cache_key = self._make_key(namespace, key)
        
        # L1: Check memory cache first (fastest)
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            
            # Check if expired
            if datetime.fromisoformat(entry["timestamp"]) + timedelta(seconds=self.memory_ttl) > datetime.now():
                logger.debug(f"💾 L1 Cache HIT: {namespace}/{key[:30]}...")
                return entry["value"]
            else:
                # Expired, remove
                del self.memory_cache[cache_key]
        
        # L2: Check Redis (slower but persistent)
        if self.redis:
            try:
                value = await self.redis.get(cache_key)
                if value:
                    logger.debug(f"📦 L2 Redis HIT: {namespace}/{key[:30]}...")
                    
                    # Parse JSON
                    parsed = json.loads(value)
                    
                    # Promote to L1 cache
                    self._set_memory(cache_key, parsed)
                    
                    return parsed
            except Exception as e:
                logger.error(f"❌ Redis get error: {e}")
        
        logger.debug(f"❌ Cache MISS: {namespace}/{key[:30]}...")
        return None
    
    
    async def set(
        self,
        namespace: str,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ):
        """
        Set cache value (L1 + L2)
        
        Args:
            namespace: Cache namespace
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            ttl: Custom TTL in seconds (optional)
        """
        
        cache_key = self._make_key(namespace, key)
        
        # L1: Set in memory
        self._set_memory(cache_key, value)
        
        # L2: Set in Redis
        if self.redis:
            try:
                redis_ttl = ttl or self.redis_ttl
                await self.redis.setex(
                    cache_key,
                    redis_ttl,
                    json.dumps(value, ensure_ascii=False)
                )
                logger.debug(f"💾 Cached in Redis: {namespace}/{key[:30]}...")
            except Exception as e:
                logger.error(f"❌ Redis set error: {e}")
    
    
    def _set_memory(self, cache_key: str, value: Any):
        """Set value in memory cache with LRU eviction"""
        
        # If memory is full, remove oldest
        if len(self.memory_cache) >= self.max_memory_items:
            # Simple LRU: Remove oldest by timestamp
            oldest_key = min(
                self.memory_cache.keys(),
                key=lambda k: self.memory_cache[k]["timestamp"]
            )
            del self.memory_cache[oldest_key]
            logger.debug("🗑️ Evicted oldest cache entry")
        
        self.memory_cache[cache_key] = {
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
    
    
    async def delete(self, namespace: str, key: str):
        """Delete from cache"""
        cache_key = self._make_key(namespace, key)
        
        # L1
        if cache_key in self.memory_cache:
            del self.memory_cache[cache_key]
        
        # L2
        if self.redis:
            try:
                await self.redis.delete(cache_key)
            except Exception as e:
                logger.error(f"❌ Redis delete error: {e}")
    
    
    async def clear_namespace(self, namespace: str):
        """Clear all keys in a namespace"""
        
        # L1: Clear memory
        keys_to_delete = [
            k for k in self.memory_cache.keys()
            if k.startswith(f"scrapigen:{namespace}:")
        ]
        for key in keys_to_delete:
            del self.memory_cache[key]
        
        # L2: Clear Redis
        if self.redis:
            try:
                pattern = f"scrapigen:{namespace}:*"
                async for key in self.redis.scan_iter(match=pattern):
                    await self.redis.delete(key)
                logger.info(f"🗑️ Cleared namespace: {namespace}")
            except Exception as e:
                logger.error(f"❌ Redis clear error: {e}")
    
    
    async def get_stats(self) -> dict:
        """Get cache statistics"""
        
        stats = {
            "memory_items": len(self.memory_cache),
            "memory_max": self.max_memory_items,
            "memory_usage_pct": len(self.memory_cache) / self.max_memory_items * 100,
            "redis_connected": self.redis is not None,
        }
        
        if self.redis:
            try:
                info = await self.redis.info("stats")
                stats["redis_keys"] = info.get("db0", {}).get("keys", 0)
                stats["redis_memory"] = info.get("used_memory_human", "unknown")
            except:
                stats["redis_keys"] = "error"
        
        return stats
    
    
    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            logger.info("👋 Redis connection closed")


# ============================================================================
# GLOBAL CACHE INSTANCE
# ============================================================================

# Initialize with environment variable or default
import os

_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get or create global cache manager"""
    global _cache_manager
    
    if _cache_manager is None:
        redis_url = os.getenv("REDIS_URL")  # e.g., "redis://localhost:6379"
        _cache_manager = CacheManager(redis_url=redis_url)
        logger.info(f"🚀 Cache initialized (Redis: {redis_url is not None})")
    
    return _cache_manager


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def cache_rendered_html(url: str, html: str, final_url: str):
    """Cache rendered HTML"""
    cache = get_cache_manager()
    await cache.set("rendered_html", url, {
        "html": html,
        "final_url": final_url,
        "timestamp": datetime.now().isoformat()
    })


async def get_cached_html(url: str) -> Optional[dict]:
    """Get cached rendered HTML"""
    cache = get_cache_manager()
    return await cache.get("rendered_html", url)


async def cache_extracted_data(url: str, prompt: str, data: list):
    """Cache extracted data"""
    cache = get_cache_manager()
    # Include prompt in key to cache different extractions separately
    key = f"{url}:{prompt}"
    await cache.set("extracted_data", key, {
        "data": data,
        "timestamp": datetime.now().isoformat()
    })


async def get_cached_extraction(url: str, prompt: str) -> Optional[dict]:
    """Get cached extraction"""
    cache = get_cache_manager()
    key = f"{url}:{prompt}"
    return await cache.get("extracted_data", key)
