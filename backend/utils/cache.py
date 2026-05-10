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


def cached(ttl: int = CACHE_TTL):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            r = await get_redis()
            if r is None:
                # No Redis — run without cache
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

            try:
                await r.setex(key, ttl, json.dumps(result, default=str))
            except Exception:
                pass

            return result
        return wrapper
    return decorator
