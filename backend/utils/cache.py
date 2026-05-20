import json
import hashlib
import os
from functools import wraps

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", 86400))

_redis = None


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


def cached(ttl: int = CACHE_TTL, degraded_ttl: int = 300):
    """Cache decorator. When the result dict contains `_degraded: True`,
    uses degraded_ttl (default 5 min) instead of ttl to avoid locking in bad data."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            r = await get_redis()
            if r is None:
                return await func(*args, **kwargs)

            cache_input = str(args) + str(sorted(kwargs.items()))
            key = f"pa:{func.__name__}:{hashlib.md5(cache_input.encode()).hexdigest()}"

            try:
                cached_val = await r.get(key)
                if cached_val:
                    return json.loads(cached_val)
            except Exception:
                pass

            result = await func(*args, **kwargs)

            actual_ttl = degraded_ttl if (isinstance(result, dict) and result.get("_degraded")) else ttl
            try:
                await r.setex(key, actual_ttl, json.dumps(result, default=str))
            except Exception:
                pass

            return result
        return wrapper
    return decorator
