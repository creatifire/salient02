"""
Admin authentication middleware for securing admin API endpoints.

This middleware provides HTTP Basic Authentication for all /api/admin/* endpoints,
ensuring only authorized administrators can access debugging and monitoring interfaces.
"""
import os
import secrets
import base64
from typing import Callable
from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import logfire


class AdminAuthMiddleware(BaseHTTPMiddleware):
    """
    HTTP Basic Auth middleware for /api/admin/* routes.
    
    Protects admin endpoints with username/password authentication.
    Credentials are configured via environment variables:
    - ADMIN_USERNAME (default: "admin")
    - ADMIN_PASSWORD (default: "changeme" - should be changed in production)
    
    Only applies to paths starting with /api/admin/
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.admin_username = os.getenv("ADMIN_USERNAME", "admin")
        self.admin_password = os.getenv("ADMIN_PASSWORD", "changeme")
        
        if self.admin_password == "changeme":
            logfire.warn(
                'security.admin_auth.default_password',
                message="Using default ADMIN_PASSWORD. Change ADMIN_PASSWORD environment variable in production."
            )
    
    async def dispatch(self, request: Request, call_next: Callable):
        """
        Check authentication for /api/admin/* requests.
        """
        # Only apply auth to admin endpoints
        if not request.url.path.startswith("/api/admin/"):
            return await call_next(request)
        
        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Basic "):
            return self._unauthorized()
        
        # Decode and validate credentials
        try:
            # Extract base64-encoded credentials
            encoded_credentials = auth_header[6:]  # Remove "Basic " prefix
            credentials = base64.b64decode(encoded_credentials).decode("utf-8")
            username, password = credentials.split(":", 1)
            
            # Use secrets.compare_digest for timing-attack resistance
            if not (secrets.compare_digest(username, self.admin_username) and 
                    secrets.compare_digest(password, self.admin_password)):
                logfire.warn(
                    'security.admin_auth.failed',
                    username=username,
                    path=request.url.path
                )
                return self._unauthorized()
            
            # Authentication successful
            logfire.info(
                'security.admin_auth.success',
                username=username,
                path=request.url.path,
                ip=request.client.host if request.client else None
            )
            
        except Exception as e:
            logfire.error(
                'security.admin_auth.error',
                error_type=type(e).__name__,
                error=str(e),
                path=request.url.path
            )
            return self._unauthorized()
        
        # Proceed to endpoint
        return await call_next(request)
    
    def _unauthorized(self):
        """Return 401 Unauthorized response with WWW-Authenticate header."""
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Admin authentication required"},
            headers={"WWW-Authenticate": 'Basic realm="Admin Area"'}
        )

