"""
Rate Limiting middleware using SlowAPI.

Provides per-user rate limiting based on user_id from request body.
Default: 60 requests/hour per user (configurable via RATE_LIMIT_PER_HOUR).
"""

import json

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.responses import JSONResponse


def _get_user_id_from_request(request: Request) -> str:
    """
    Extract user_id from the JSON request body for rate limiting.
    
    Falls back to IP address if user_id isn't available.
    This function is synchronous — SlowAPI requires it.
    We cache the parsed body on the request state.
    """
    # Try to get cached body from request state
    if hasattr(request.state, '_parsed_body'):
        body = request.state._parsed_body
        if isinstance(body, dict) and "user_id" in body:
            return f"user:{body['user_id']}"
    
    # Fallback to IP-based limiting
    return get_remote_address(request)


# Create the limiter instance with in-memory storage
limiter = Limiter(
    key_func=_get_user_id_from_request,
    storage_uri="memory://",
    strategy="fixed-window",
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Custom handler for rate limit exceeded errors."""
    # Extract retry-after from the exception
    retry_after = getattr(exc, 'retry_after', 60)
    
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please slow down.",
            "retry_after": retry_after,
            "limit": str(exc.detail) if hasattr(exc, 'detail') else "60 per hour",
        },
        headers={
            "Retry-After": str(retry_after),
        },
    )
