"""
Structured logging with correlation IDs and secret redaction.
"""
import logging
import json
import uuid
import sys
import re
from typing import Any, Dict, Optional, Union
from datetime import datetime
from contextvars import ContextVar
from pythonjsonlogger import jsonlogger

# Context variable for correlation ID
correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)

# Patterns for secrets that should be redacted
SECRET_PATTERNS = [
    (re.compile(r'(?i)(api[_-]?key|apikey|token|secret|password|passwd|auth[_-]?token)\s*[:=]\s*["\']?([^"\'\s,}]+)'), r'\1=***REDACTED***'),
    (re.compile(r'(?i)(authorization|bearer)\s+([^\s,}]+)'), r'\1 ***REDACTED***'),
    (re.compile(r'X-Local-API-Token["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)'), r'X-Local-API-Token=***REDACTED***'),
    (re.compile(r'LOCAL_API_TOKEN["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)'), r'LOCAL_API_TOKEN=***REDACTED***'),
    (re.compile(r'[a-f0-9]{64}'), r'***REDACTED_HASH***'),  # 64-char hex (SHA256/token)
    (re.compile(r'[a-f0-9]{32}'), r'***REDACTED_TOKEN***'),  # 32-char hex (shorter token)
    (re.compile(r'sk-[a-zA-Z0-9]{32,}'), r'***REDACTED_OPENAI_KEY***'),  # OpenAI-style keys
    (re.compile(r'gh[pousr]_[a-zA-Z0-9]{36,}'), r'***REDACTED_GITHUB_TOKEN***'),  # GitHub tokens
]


class RedactingFormatter(jsonlogger.JsonFormatter):
    """JSON formatter that redacts secrets from log output."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        super().add_fields(log_record, record, message_dict)
        
        # Add correlation ID if available
        corr_id = correlation_id_var.get()
        if corr_id:
            log_record["correlation_id"] = corr_id
        
        # Add timestamp
        log_record["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        # Add level
        log_record["level"] = record.levelname
        
        # Redact message
        if "message" in log_record:
            log_record["message"] = self._redact(log_record["message"])
        
        # Redact all string fields
        for key, value in log_record.items():
            if isinstance(value, str):
                log_record[key] = self._redact(value)
            elif isinstance(value, dict):
                log_record[key] = self._redact_dict(value)
            elif isinstance(value, list):
                log_record[key] = [self._redact(v) if isinstance(v, str) else v for v in value]

    def _redact(self, text: str) -> str:
        """Redact secrets from a string."""
        if not isinstance(text, str):
            return text
        redacted = text
        for pattern, replacement in SECRET_PATTERNS:
            redacted = pattern.sub(replacement, redacted)
        return redacted

    def _redact_dict(self, d: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively redact secrets in a dictionary."""
        result = {}
        for key, value in d.items():
            if isinstance(value, str):
                result[key] = self._redact(value)
            elif isinstance(value, dict):
                result[key] = self._redact_dict(value)
            elif isinstance(value, list):
                result[key] = [self._redact(v) if isinstance(v, str) else v for v in value]
            else:
                result[key] = value
        return result


class CorrelationIdFilter(logging.Filter):
    """Filter that adds correlation ID to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        corr_id = correlation_id_var.get()
        if corr_id:
            record.correlation_id = corr_id
        else:
            record.correlation_id = "none"
        return True


def setup_logging(
    level: int = logging.INFO,
    json_format: bool = True,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Set up structured logging with correlation IDs and secret redaction.
    
    Args:
        level: Log level
        json_format: Use JSON format (True) or human-readable (False)
        log_file: Optional file path for file logging
    
    Returns:
        Configured root logger
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Add correlation ID filter
    root_logger.addFilter(CorrelationIdFilter())
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    if json_format:
        formatter = RedactingFormatter(
            "%(timestamp)s %(level)s %(name)s %(correlation_id)s %(message)s"
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s [%(correlation_id)s] %(message)s"
        )
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(RedactingFormatter(
            "%(timestamp)s %(level)s %(name)s %(correlation_id)s %(message)s"
        ))
        root_logger.addHandler(file_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    return root_logger


def set_correlation_id(corr_id: Optional[str] = None) -> str:
    """Set correlation ID for current context. Returns the ID used."""
    if corr_id is None:
        corr_id = str(uuid.uuid4())[:8]
    correlation_id_var.set(corr_id)
    return corr_id


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID."""
    return correlation_id_var.get()


def clear_correlation_id():
    """Clear correlation ID."""
    correlation_id_var.set(None)


class LoggingMiddleware:
    """ASGI middleware for request logging with correlation IDs."""
    
    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger("backend.requests")
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Generate correlation ID
        corr_id = set_correlation_id()
        
        # Log request
        path = scope.get("path", "")
        method = scope.get("method", "")
        client = scope.get("client")
        
        if client:
            client_ip, client_port = client[0], client[1]
        else:
            client_ip, client_port = "unknown", 0
        
        self.logger.info(
            f"Request started: {method} {path} from {client_ip}:{client_port}",
            extra={
                "method": method,
                "path": path,
                "client_ip": client_ip,
                "client_port": client_port,
            }
        )
        
        # Track response
        response_started = False
        status_code = 500
        
        async def send_wrapper(message):
            nonlocal response_started, status_code
            if message["type"] == "http.response.start":
                response_started = True
                status_code = message["status"]
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            self.logger.error(
                f"Request failed: {method} {path} - {e}",
                extra={"method": method, "path": path, "error": str(e)}
            )
            raise
        finally:
            self.logger.info(
                f"Request completed: {method} {path} -> {status_code}",
                extra={"method": method, "path": path, "status_code": status_code}
            )
            clear_correlation_id()


def log_with_context(logger: logging.Logger, level: int, message: str, **context):
    """Log with additional context fields."""
    logger.log(level, message, extra=context)