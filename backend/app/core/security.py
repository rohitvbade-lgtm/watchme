import time
import logging
from collections import deque
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response
from app.config import get_settings

logger = logging.getLogger(__name__)


def get_client_ip(request: Request) -> str:
    """
    Extract the real client IP address, respecting reverse proxies (Caddy, Cloudflare, Nginx).
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # X-Forwarded-For can be a comma-separated list; first entry is the client IP
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
        
    return request.client.host if request.client else "unknown"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Injects industry-standard HTTP security headers into every response.
    Protects against MIME sniffing, clickjacking, and cross-site scripting.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        
        # Enforce HSTS for HTTPS connections
        if request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            
        return response


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Lightweight, in-memory sliding-window rate limiter.
    Zero external dependencies, minimal memory footprint.
    Protects upstream APIs (TMDB, Groq) and Oracle VM resources from spam or DDoS.
    """
    def __init__(self, app):
        super().__init__(app)
        # ip -> deque of timestamps
        self._history: Dict[str, deque] = {}
        self._last_cleanup = time.time()
        
    def _clean_stale_records(self, now: float):
        """Purge entries older than 60 seconds to prevent memory leaks."""
        if now - self._last_cleanup < 300:  # Run cleanup at most once every 5 minutes
            return
        self._last_cleanup = now
        stale_ips = []
        for ip, timestamps in self._history.items():
            while timestamps and now - timestamps[0] > 60:
                timestamps.popleft()
            if not timestamps:
                stale_ips.append(ip)
        for ip in stale_ips:
            del self._history[ip]

    async def dispatch(self, request: Request, call_next) -> Response:
        settings = get_settings()
        if not settings.rate_limit_enabled:
            return await call_next(request)

        # Exempt CORS preflight requests — must reach CORSMiddleware before being counted
        if request.method == "OPTIONS":
            return await call_next(request)

        # Exempt health check and docs
        path = request.url.path
        if path == "/health" or path.startswith("/docs") or path.startswith("/openapi.json"):
            return await call_next(request)

        client_ip = get_client_ip(request)
        now = time.time()
        self._clean_stale_records(now)

        # Determine rate limit based on endpoint sensitivity
        if path.startswith("/api/search"):
            limit = settings.rate_limit_search_per_minute
        elif path.startswith("/api/notifications/test"):
            limit = 10
        else:
            limit = settings.rate_limit_per_minute

        history_key = f"{client_ip}:{path.split('/')[2] if len(path.split('/')) > 2 else 'root'}"
        timestamps = self._history.setdefault(history_key, deque())

        # Discard hits older than 60 seconds
        while timestamps and now - timestamps[0] > 60:
            timestamps.popleft()

        if len(timestamps) >= limit:
            logger.warning(f"Rate limit exceeded for {client_ip} on {path} ({len(timestamps)}/{limit} req/min)")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many requests. Please slow down and try again later."},
                headers={"Retry-After": "60"}
            )

        timestamps.append(now)
        return await call_next(request)


class ApiKeyAuthMiddleware(BaseHTTPMiddleware):
    """
    Optional API Key verification.
    If API_SECRET_KEY is configured in .env, validates 'x-api-key' or Bearer header
    on all /api routes. If not configured, allows all requests.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        settings = get_settings()
        secret_key = settings.api_secret_key

        if not secret_key:
            return await call_next(request)

        path = request.url.path
        # Only enforce on /api routes, exempt health check and documentation
        if not path.startswith("/api"):
            return await call_next(request)

        # Check options request (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        api_key = request.headers.get("x-api-key")
        auth_header = request.headers.get("authorization")
        if not api_key and auth_header and auth_header.lower().startswith("bearer "):
            api_key = auth_header[7:].strip()

        if not api_key or api_key != secret_key:
            logger.warning(f"Unauthorized request to {path} from {get_client_ip(request)}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Unauthorized: Invalid or missing API key."}
            )

        return await call_next(request)
