"""
Middleware package for request/response processing.

This package contains middleware components for:
- Session management and automatic session creation
- Request logging and monitoring
- Security headers and CORS handling
- Rate limiting and request validation

Middleware is executed in order of registration and follows FastAPI patterns.
"""

from .session_middleware import SessionMiddleware

__all__ = ["SessionMiddleware"]
