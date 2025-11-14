"""
Admin authentication middleware for securing admin API endpoints.

This middleware provides session-based authentication for all /api/admin/* endpoints,
ensuring only authorized administrators can access debugging and monitoring interfaces.
"""
import os
from datetime import datetime, timezone
from typing import Callable
from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import logfire


class AdminAuthMiddleware(BaseHTTPMiddleware):
    """
    Session-based authentication middleware for /api/admin/* routes.
    
    Protects admin endpoints by checking session authentication.
    Users must first login via POST /api/admin/login to set session.
    
    Session expires after ADMIN_SESSION_EXPIRY_MINUTES (default: 120).
    
    Only applies to paths starting with /api/admin/ (except /api/admin/login)
    """
    
    def __init__(self, app):
        super().__init__(app)
        admin_password = os.getenv("ADMIN_PASSWORD", "changeme")
        
        if admin_password == "changeme":
            logfire.warn(
                'security.admin_auth.default_password',
                message="Using default ADMIN_PASSWORD. Change ADMIN_PASSWORD environment variable in production."
            )
    
    async def dispatch(self, request: Request, call_next: Callable):
        """
        Check session authentication for /api/admin/* requests.
        """
        # Skip auth check for login endpoint itself
        if request.url.path == "/api/admin/login":
            return await call_next(request)
        
        # Only apply auth to other admin endpoints
        if not request.url.path.startswith("/api/admin/"):
            return await call_next(request)
        
        # Check session authentication
        if not request.session.get("admin_authenticated"):
            logfire.warn(
                'security.admin_auth.not_authenticated',
                path=request.url.path,
                ip=request.client.host if request.client else None
            )
            return self._unauthorized("Not authenticated")
        
        # Check session expiry
        expiry_str = request.session.get("admin_expiry")
        if expiry_str:
            try:
                expiry = datetime.fromisoformat(expiry_str)
                if datetime.now(timezone.utc) > expiry:
                    # Session expired, clear it
                    del request.session["admin_authenticated"]
                    del request.session["admin_expiry"]
                    logfire.warn(
                        'security.admin_auth.session_expired',
                        path=request.url.path,
                        expiry=expiry_str
                    )
                    return self._unauthorized("Session expired")
            except Exception as e:
                # Invalid expiry format, clear session
                logfire.error(
                    'security.admin_auth.invalid_expiry',
                    error=str(e),
                    expiry_str=expiry_str
                )
                if "admin_authenticated" in request.session:
                    del request.session["admin_authenticated"]
                if "admin_expiry" in request.session:
                    del request.session["admin_expiry"]
                return self._unauthorized("Invalid session")
        
        # Authentication valid
        logfire.debug(
            'security.admin_auth.session_valid',
            path=request.url.path
        )
        
        # Proceed to endpoint
        return await call_next(request)
    
    def _unauthorized(self, message: str = "Admin authentication required"):
        """Return 401 Unauthorized response."""
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": message, "login_required": True}
        )

