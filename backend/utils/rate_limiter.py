import asyncio
import os
import time
from collections import defaultdict
from datetime import datetime, timezone

_DAILY_LIMIT = 5
_store: dict[str, list[float]] = defaultdict(list)
_lock = asyncio.Lock()

# Comma-separated IPs that bypass rate limiting (set RATE_LIMIT_WHITELIST in Railway env vars)
_WHITELIST: set[str] = {
    ip.strip()
    for ip in os.getenv("RATE_LIMIT_WHITELIST", "").split(",")
    if ip.strip()
}


def get_client_ip(request) -> str:
    """Extract client IP, using the rightmost entry in X-Forwarded-For (Railway appends real IP last)."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take rightmost IP — the one Railway's proxy appended, which cannot be spoofed
        return forwarded.split(",")[-1].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "unknown"


async def check_rate_limit(ip: str) -> tuple[bool, int]:
    """Check if IP is within daily limit. Returns (allowed, remaining). Thread-safe."""
    if ip in _WHITELIST:
        return True, _DAILY_LIMIT  # whitelisted IPs always allowed, full quota shown
    async with _lock:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        key = f"{today}:{ip}"
        used = len(_store[key])
        if used >= _DAILY_LIMIT:
            return False, 0
        _store[key].append(time.time())
        return True, _DAILY_LIMIT - used - 1


def get_usage(ip: str) -> dict:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    key = f"{today}:{ip}"
    used = len(_store[key])
    return {"used": used, "limit": _DAILY_LIMIT, "remaining": max(0, _DAILY_LIMIT - used)}
