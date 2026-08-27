"""
rate_limiter.py - Redis-backed Sliding Window Rate Limiter for SynapseAir
"""
import time
from typing import Optional, Dict
from dataclasses import dataclass, field

try:
    import redis.asyncio as aioredis
    _REDIS_AVAILABLE = True
except ImportError:
    _REDIS_AVAILABLE = False


@dataclass
class RateLimitConfig:
    max_requests: int
    window_seconds: int
    key_prefix: str = "rl"


DEFAULT_LIMITS = {
    "webhook": RateLimitConfig(max_requests=10, window_seconds=60, key_prefix="rl:webhook"),
    "consensus": RateLimitConfig(max_requests=50, window_seconds=60, key_prefix="rl:consensus"),
    "history": RateLimitConfig(max_requests=100, window_seconds=60, key_prefix="rl:history"),
    "stream": RateLimitConfig(max_requests=30, window_seconds=60, key_prefix="rl:stream"),
    "system": RateLimitConfig(max_requests=60, window_seconds=60, key_prefix="rl:system"),
    "default": RateLimitConfig(max_requests=120, window_seconds=60, key_prefix="rl:default"),
}


@dataclass
class RateLimitResult:
    allowed: bool
    remaining: int
    retry_after_seconds: float = 0.0
    limit: int = 0
    window_seconds: int = 0


class RateLimiter:
    """Sliding window rate limiter with Redis or in-memory backend."""

    def __init__(self, redis_url=None, limits=None):
        self._redis = None
        self._redis_url = redis_url
        self._limits = limits or DEFAULT_LIMITS
        self._memory_store: Dict[str, list] = {}

    async def _get_redis(self):
        if self._redis is None and self._redis_url and _REDIS_AVAILABLE:
            try:
                self._redis = aioredis.from_url(self._redis_url, decode_responses=True)
                await self._redis.ping()
            except Exception:
                self._redis = None
        return self._redis

    def _get_config(self, category):
        return self._limits.get(category, self._limits["default"])

    async def check(self, client_id: str, category: str = "default") -> RateLimitResult:
        config = self._get_config(category)
        key = f"{config.key_prefix}:{client_id}"
        now = time.time()
        window_start = now - config.window_seconds
        redis = await self._get_redis()
        if redis:
            return await self._check_redis(redis, key, config, now, window_start)
        return self._check_memory(key, config, now, window_start)

    async def _check_redis(self, redis, key, config, now, window_start):
        pipe = redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {f"{now}:{id(now)}": now})
        pipe.expire(key, config.window_seconds + 10)
        results = await pipe.execute()
        current_count = results[1]
        if current_count >= config.max_requests:
            oldest = await redis.zrange(key, 0, 0, withscores=True)
            retry_after = (oldest[0][1] + config.window_seconds - now) if oldest else config.window_seconds
            return RateLimitResult(allowed=False, remaining=0, retry_after_seconds=max(0, retry_after),
                                   limit=config.max_requests, window_seconds=config.window_seconds)
        return RateLimitResult(allowed=True, remaining=config.max_requests - current_count - 1,
                               limit=config.max_requests, window_seconds=config.window_seconds)

    def _check_memory(self, key, config, now, window_start):
        if key not in self._memory_store:
            self._memory_store[key] = []
        self._memory_store[key] = [t for t in self._memory_store[key] if t > window_start]
        current_count = len(self._memory_store[key])
        if current_count >= config.max_requests:
            retry_after = (self._memory_store[key][0] + config.window_seconds - now) if self._memory_store[key] else 0
            return RateLimitResult(allowed=False, remaining=0, retry_after_seconds=max(0, retry_after),
                                   limit=config.max_requests, window_seconds=config.window_seconds)
        self._memory_store[key].append(now)
        return RateLimitResult(allowed=True, remaining=config.max_requests - current_count - 1,
                               limit=config.max_requests, window_seconds=config.window_seconds)

    async def reset(self, client_id, category="default"):
        config = self._get_config(category)
        key = f"{config.key_prefix}:{client_id}"
        redis = await self._get_redis()
        if redis:
            await redis.delete(key)
        else:
            self._memory_store.pop(key, None)

    async def close(self):
        if self._redis:
            await self._redis.close()
            self._redis = None


_global_limiter = None


def get_rate_limiter(redis_url=None) -> RateLimiter:
    global _global_limiter
    if _global_limiter is None:
        _global_limiter = RateLimiter(redis_url=redis_url)
    return _global_limiter
