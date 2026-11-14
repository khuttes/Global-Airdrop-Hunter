"""
Rate limiting middleware for API access control.
"""
import time
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class TokenBucketRateLimiter:
    """Thread-safe token bucket rate limiter per token."""

    def __init__(self, requests_per_minute: int = 60, burst: int = 10):
        self.requests_per_minute = requests_per_minute
        self.burst = burst
        self.refill_rate = requests_per_minute / 60.0  # tokens per second
        self.buckets: Dict[str, Tuple[float, float]] = {}  # token -> (tokens, last_refill)
        self._cleanup_interval = 300  # 5 minutes
        self._last_cleanup = time.time()

    def _refill(self, token: str) -> float:
        """Refill tokens for a bucket and return current tokens."""
        now = time.time()
        tokens, last_refill = self.buckets.get(token, (self.burst, now))
        
        elapsed = now - last_refill
        tokens = min(self.burst, tokens + elapsed * self.refill_rate)
        
        self.buckets[token] = (tokens, now)
        return tokens

    def consume(self, token: str, tokens: int = 1) -> bool:
        """Try to consume tokens. Returns True if successful."""
        current = self._refill(token)
        if current >= tokens:
            self.buckets[token] = (current - tokens, time.time())
            return True
        return False

    def get_remaining(self, token: str) -> int:
        """Get remaining tokens for a token."""
        return int(self._refill(token))

    def cleanup(self):
        """Remove old buckets."""
        now = time.time()
        if now - self._last_cleanup > self._cleanup_interval:
            # Remove buckets not used in last 10 minutes
            cutoff = now - 600
            self.buckets = {
                k: v for k, v in self.buckets.items()
                if v[1] > cutoff
            }
            self._last_cleanup = now


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware for API endpoints."""

    def __init__(self, app, requests_per_minute: int = 60, burst: int = 10):
        super().__init__(app)
        self.limiter = TokenBucketRateLimiter(requests_per_minute, burst)
        self.exempt_paths = {
            "/api/v1/health",
            "/api/v1/launch",
            "/docs",
            "/redoc",
            "/openapi.json",
        }
        self.exempt_prefixes = ("/css/", "/js/", "/favicon.ico", "/assets/", "/images/", "/fonts/")

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip exempt paths
        if path in self.exempt_paths:
            return await call_next(request)

        for prefix in self.exempt_prefixes:
            if path.startswith(prefix):
                return await call_next(request)

        if path == "/":
            return await call_next(request)

        # Get token for rate limiting
        auth_header = request.headers.get("X-Local-API-Token")
        if not auth_header:
            return await call_next(request)  # Let auth middleware handle missing token

        # Check rate limit
        if not self.limiter.consume(auth_header):
            remaining = self.limiter.get_remaining(auth_header)
            logger.warning(f"Rate limit exceeded for token ending in ...{auth_header[-8:]} on {path}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please slow down.",
                        "retry_after": 60
                    }
                },
                headers={
                    "X-RateLimit-Remaining": str(remaining),
                    "X-RateLimit-Limit": str(self.limiter.requests_per_minute),
                    "Retry-After": "60",
                }
            )

        response = await call_next(request)

        # Add rate limit headers
        remaining = self.limiter.get_remaining(auth_header)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Limit"] = str(self.limiter.requests_per_minute)

        # Periodic cleanup
        self.limiter.cleanup()

        return response


# Global rate limiter instance
rate_limiter = TokenBucketRateLimiter(requests_per_minute=60, burst=10)