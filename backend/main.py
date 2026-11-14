import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.config import get_settings
from backend.core.security import token_manager, create_token_hash
from backend.core.structured_logging import setup_logging, LoggingMiddleware
from backend.database import init_database, run_migrations
from backend.api import api_router
from backend.api.middleware.auth import AuthMiddleware
from backend.api.middleware.rate_limit import RateLimitMiddleware


# Set up structured logging
setup_logging(
    level=logging.INFO,
    json_format=True,
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Global Airdrop Hunter API...")
    try:
        init_database()
        run_migrations()
        
        # Use token from environment (passed by Electron) or generate new one
        existing_token = os.environ.get("LOCAL_API_TOKEN")
        if existing_token:
            api_token = existing_token
            token_manager._token = api_token
            token_manager._token_hash = create_token_hash(api_token)
            token_manager._created_at = datetime.utcnow()
            logger.info("Using API token from environment")
        else:
            api_token = token_manager.generate()
            logger.info(f"API Token generated: {api_token}")
        
        os.environ["LOCAL_API_TOKEN"] = api_token
        logger.info("Database initialized and migrations applied")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    yield

    logger.info("Shutting down Global Airdrop Hunter API...")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Local API for Global Airdrop Hunter desktop application",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:*", "http://localhost:*", "file://"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Security middleware (order matters: auth first, then rate limit)
    app.add_middleware(AuthMiddleware)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=60, burst=10)
    
    # Request logging middleware
    app.add_middleware(LoggingMiddleware)

    app.include_router(api_router)

    # Serve frontend static files
    frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
    if os.path.exists(frontend_dir):
        app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.exception(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}},
        )

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )