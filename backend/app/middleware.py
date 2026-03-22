"""Demo PIN authentication middleware."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings

# Paths that bypass PIN check
_PUBLIC_PATHS = ("/api/health",)


class DemoPinMiddleware(BaseHTTPMiddleware):
    """Check X-Demo-Token header (or ?token= param) against DEMO_PIN.

    If DEMO_PIN is empty, all requests pass through (dev mode).
    """

    async def dispatch(self, request: Request, call_next):
        if not settings.demo_pin:
            return await call_next(request)

        path = request.url.path
        if not path.startswith("/api/") or path in _PUBLIC_PATHS:
            return await call_next(request)

        token = request.headers.get("x-demo-token") or request.query_params.get("token")
        if token != settings.demo_pin:
            return JSONResponse({"detail": "Invalid demo token"}, status_code=401)

        return await call_next(request)
