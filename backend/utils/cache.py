import json
import hashlib
import os
import time
from functools import wraps

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", 86400))
CACHE_VERSION = os.getenv("CACHE_VERSION", "2026-05-21-area-verda-v2")

_redis = None

# In-memory fallback cache used when Redis is unavailable (e.g., Railway without Redis addon).
# Entries: {key: (value_json, expires_at_unix)}
# Capped at 200 entries to avoid unbounded memory growth on a single Railway dyno.
_MEM_CACHE: dict[str, tuple[str, float]] = {}
_MEM_CACHE_MAX = 200


async def get_redis():
    global _redis
    if _redis is None:
        try:
            import redis.asyncio as redis
            _redis = await redis.from_url(REDIS_URL)
            await _redis.ping()
        except Exception:
            _redis = None
    return _redis


def _mem_get(key: str) -> str | None:
    entry = _MEM_CACHE.get(key)
    if entry is None:
        return None
    val, exp = entry
    if time.time() > exp:
        _MEM_CACHE.pop(key, None)
        return None
    return val


def _mem_set(key: str, value: str, ttl: int) -> None:
    # Evict oldest entry when at capacity
    if len(_MEM_CACHE) >= _MEM_CACHE_MAX:
        oldest = min(_MEM_CACHE, key=lambda k: _MEM_CACHE[k][1])
        _MEM_CACHE.pop(oldest, None)
    _MEM_CACHE[key] = (value, time.time() + ttl)


def cached(ttl: int = CACHE_TTL, degraded_ttl: int = 300):
    """Cache decorator with Redis primary + in-memory fallback.

    When the result dict contains `_degraded: True`, uses degraded_ttl (default 5 min)
    so failed Overpass queries don't lock in stale data for 24 hours.
    Falls back to an in-memory LRU-ish dict when Redis is unavailable (Railway without addon).
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_input = CACHE_VERSION + str(args) + str(sorted(kwargs.items()))
            key = f"pa:{func.__name__}:{hashlib.md5(cache_input.encode()).hexdigest()}"

            r = await get_redis()

            # Read from Redis or memory
            if r is not None:
                try:
                    cached_val = await r.get(key)
                    if cached_val:
                        return json.loads(cached_val)
                except Exception:
                    pass
            else:
                cached_val = _mem_get(key)
                if cached_val:
                    return json.loads(cached_val)

            result = await func(*args, **kwargs)
            actual_ttl = degraded_ttl if (isinstance(result, dict) and result.get("_degraded")) else ttl
            serialized = json.dumps(result, default=str)

            # Write to Redis or memory
            if r is not None:
                try:
                    await r.setex(key, actual_ttl, serialized)
                except Exception:
                    pass
            else:
                _mem_set(key, serialized, actual_ttl)

            return result
        return wrapper
    return decorator
