"""Rate limiting básico (ventana fija por minuto) con Redis y fallback en memoria.

El borde (Cloudflare WAF) es la primera línea de defensa; este middleware es
defensa en profundidad para el propio origen. Limites por ruta:
  /v1/storefront/*  300 req/min por IP
  /v1/admin/*       120 req/min por IP
  /v1/platform/*     30 req/min por IP
Si Redis no está configurado, el límite se aplica en memoria (por proceso).
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass

import structlog
from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings

logger = structlog.get_logger("growup.ratelimit")

_LIMITS: tuple[tuple[str, int], ...] = (
    ("/v1/platform", 30),
    ("/v1/admin", 120),
    ("/v1/onboarding", 10),
    ("/v1/storefront", 300),
)


@dataclass
class _MemoryBucket:
    count: int = 0
    reset_at: float = 0.0


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._buckets: dict[str, _MemoryBucket] = defaultdict(_MemoryBucket)

    async def hit(self, key: str, limit: int, window_seconds: int = 60) -> tuple[bool, int]:
        now = time.monotonic()
        bucket = self._buckets[key]
        if now >= bucket.reset_at:
            bucket.count = 0
            bucket.reset_at = now + window_seconds
        bucket.count += 1
        remaining = max(0, limit - bucket.count)
        return bucket.count <= limit, remaining


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_url: str | None = None) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self._redis_url = redis_url
        self._memory = InMemoryRateLimiter()
        self._client: Redis | None = None
        self._redis_failed = False

    async def _redis(self) -> Redis | None:
        if self._client is None and self._redis_url and not self._redis_failed:
            try:
                import redis.asyncio as aioredis

                self._client = aioredis.from_url(  # type: ignore[no-untyped-call]
                    self._redis_url, socket_timeout=1.0, decode_responses=True
                )
            except Exception:
                logger.warning("ratelimit_redis_unavailable")
                self._redis_failed = True
        return self._client

    async def _hit(self, key: str, limit: int) -> tuple[bool, int]:
        client = await self._redis()
        if client is not None:
            window = int(time.time() // 60)
            redis_key = f"rl:{window}:{key}"
            try:
                count = await client.incr(redis_key)
                if count == 1:
                    await client.expire(redis_key, 120)
                remaining = max(0, limit - count)
                return count <= limit, remaining
            except Exception:
                logger.warning("ratelimit_redis_error", exc_info=True)
                self._redis_failed = True
        return await self._memory.hit(key, limit)

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        if settings.environment == "test":
            return await call_next(request)
        path = request.url.path
        limit = next((value for prefix, value in _LIMITS if path.startswith(prefix)), None)
        if limit is None:
            return await call_next(request)

        ip = request.client.host if request.client else "unknown"
        allowed, remaining = await self._hit(f"{path.split('/')[1]}-{ip}", limit)
        if not allowed:
            return JSONResponse(
                status_code=429,
                headers={"Retry-After": "60", "X-RateLimit-Limit": str(limit)},
                content={
                    "error": {
                        "code": "RATE_LIMITED",
                        "message": "Demasiadas solicitudes, intenta de nuevo en un minuto",
                        "details": {"retry_after": 60},
                        "request_id": getattr(request.state, "request_id", None),
                    }
                },
            )
        response: Response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
