"""
Global configuration and health check endpoints.
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import logfire

from ..config import load_config
from ..database import get_database_service

router = APIRouter(tags=["system"])


@router.get("/health")
async def health_check():
    """
    Comprehensive health check for the application.
    
    Verifies database connectivity and application status.
    """
    health_status = {
        "status": "healthy",
        "database": "unknown",
        "version": "1.0.0"
    }
    
    try:
        # Check database connectivity
        db_service = get_database_service()
        is_db_up = await db_service.check_health()
        health_status["database"] = "up" if is_db_up else "down"
        if not is_db_up:
            health_status["status"] = "degraded"
    except Exception as e:
        logfire.error('health_check.db_error', error=str(e))
        health_status["database"] = "error"
        health_status["status"] = "unhealthy"
        
    return JSONResponse(
        content=health_status,
        status_code=200 if health_status["status"] != "unhealthy" else 503
    )


@router.get("/api/config")
async def get_ui_config():
    """
    Get UI-related configuration for the frontend widget.
    """
    config = load_config()
    ui_config = config.get("ui", {})
    
    # Return a subset of config safe for frontend exposure
    return {
        "ui": {
            "sse_enabled": ui_config.get("sse_enabled", True),
            "allow_basic_html": ui_config.get("allow_basic_html", True),
            "frontend_debug": ui_config.get("frontend_debug", False)
        }
    }
