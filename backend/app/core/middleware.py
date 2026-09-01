import time
import uuid
import re
from typing import Dict, Tuple
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from backend.app.core.config import settings
from backend.app.core.logging_config import set_correlation_id, get_correlation_id, logger


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Injects and propagates unique request correlation IDs for end-to-end tracing.
    """
    async def dispatch(self, request: Request, call_next):
        header_name = settings.CORRELATION_ID_HEADER
        cid = request.headers.get(header_name)
        if not cid:
            cid = f"AGNI-{uuid.uuid4().hex[:12].upper()}"

        set_correlation_id(cid)
        t_start = time.perf_counter()

        response: Response = await call_next(request)

        latency_ms = round((time.perf_counter() - t_start) * 1000.0, 2)
        response.headers[header_name] = cid
        response.headers["X-Response-Time-Ms"] = str(latency_ms)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Applies production security headers to prevent clickjacking, MIME sniffing, and XSS.
    """
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    In-memory rate limiter protecting public and authenticated API endpoints.
    """
    def __init__(self, app, max_requests_per_minute: int = 120):
        super().__init__(app)
        self.max_requests = max_requests_per_minute
        self.request_records: Dict[str, list] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Exclude internal health and docs endpoints from rate limiting
        path = request.url.path
        if path.startswith("/health") or path.startswith("/api/v1/health") or path.startswith("/api/v1/docs") or path.startswith("/api/v1/openapi.json"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Clean old timestamps (> 60s)
        recent_timestamps = [t for t in self.request_records[client_ip] if now - t < 60.0]
        self.request_records[client_ip] = recent_timestamps

        if len(recent_timestamps) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for IP {client_ip} on path {path}")
            return JSONResponse(
                status_code=429,
                content={
                    "status": "RATE_LIMIT_EXCEEDED",
                    "detail": f"Rate limit of {self.max_requests} requests per minute exceeded. Please try again later.",
                    "correlation_id": get_correlation_id()
                },
                headers={"Retry-After": "60", settings.CORRELATION_ID_HEADER: get_correlation_id()}
            )

        self.request_records[client_ip].append(now)
        return await call_next(request)


class SafeExceptionMiddleware(BaseHTTPMiddleware):
    """
    Catches unhandled exceptions, logs internal details with correlation IDs,
    and returns sanitized client error responses without leaking internal credentials.
    """
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            cid = get_correlation_id()
            logger.error(f"Unhandled exception during {request.method} {request.url.path} [CID:{cid}]: {exc}", exc_info=True)
            
            # Sanitize message to prevent database connection string or internal path exposure
            safe_message = "An internal server error occurred while processing the operational request."
            if "psycopg2" in str(exc) or "sqlalchemy" in str(exc).lower():
                safe_message = "A database connectivity or query execution error occurred. Operational audit logged."

            return JSONResponse(
                status_code=500,
                content={
                    "status": "INTERNAL_SERVER_ERROR",
                    "detail": safe_message,
                    "correlation_id": cid
                },
                headers={settings.CORRELATION_ID_HEADER: cid}
            )
