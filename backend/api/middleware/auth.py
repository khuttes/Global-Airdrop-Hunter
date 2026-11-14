from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from backend.core.security import token_manager
import logging

logger = logging.getLogger(__name__)

EXEMPT_PATHS = {
    "/api/v1/health",
    "/api/v1/launch",
    "/docs",
    "/redoc",
    "/openapi.json",
}

# Paths that are allowed without auth (static files, frontend)
EXEMPT_PREFIXES = (
    "/css/",
    "/js/",
    "/favicon.ico",
    "/assets/",
    "/images/",
    "/fonts/",
)

MAX_REQUEST_SIZE = 1024 * 1024  # 1 MB


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Allow exempt paths
        if path in EXEMPT_PATHS:
            return await call_next(request)

        # Allow static file paths (frontend assets)
        for prefix in EXEMPT_PREFIXES:
            if path.startswith(prefix):
                return await call_next(request)

        # Allow root path for frontend (serves index.html)
        if path == "/":
            return await call_next(request)

        # Check request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_REQUEST_SIZE:
            logger.warning(f"Request too large: {content_length} bytes for {path} from {request.client.host if request.client else 'unknown'}")
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"error": {"code": "PAYLOAD_TOO_LARGE", "message": f"Request body exceeds maximum size of {MAX_REQUEST_SIZE} bytes"}},
            )

        auth_header = request.headers.get("X-Local-API-Token")
        if not auth_header:
            logger.warning(f"Missing auth token for {path} from {request.client.host if request.client else 'unknown'}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": {"code": "MISSING_TOKEN", "message": "Missing X-Local-API-Token header"}},
            )

        if not token_manager.validate(auth_header):
            logger.warning(f"Invalid auth token for {path} from {request.client.host if request.client else 'unknown'}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": {"code": "INVALID_TOKEN", "message": "Invalid or expired API token"}},
            )

        origin = request.headers.get("Origin") or request.headers.get("Referer")
        if origin:
            if not (origin.startswith("http://127.0.0.1:") or origin.startswith("http://localhost:") or origin.startswith("file://")):
                logger.warning(f"Invalid origin: {origin} for {path}")
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"error": {"code": "INVALID_ORIGIN", "message": "Invalid request origin"}},
                )

        return await call_next(request)