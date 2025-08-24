"""
Test module for session middleware functionality.

This test verifies that the session middleware:
- Auto-creates sessions for new requests
- Loads existing sessions from cookies
- Updates session activity on each request
- Sets session cookies properly
- Provides session context to route handlers
"""

import asyncio
from typing import Dict, Any
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from ..database import get_database_service, initialize_database, shutdown_database
from .session_middleware import SessionMiddleware, get_current_session


def create_test_app() -> FastAPI:
    """Create a test FastAPI app with session middleware."""
    app = FastAPI()
    
    # Add session middleware
    app.add_middleware(SessionMiddleware)
    
    @app.get("/test")
    async def test_endpoint(request: Request):
        """Test endpoint that returns session info."""
        session = get_current_session(request)
        if session:
            return {
                "session_id": str(session.id),
                "session_key": session.session_key[:8] + "...",
                "is_anonymous": session.is_anonymous,
                "has_session": True
            }
        return {"has_session": False}
    
    @app.get("/excluded")
    async def excluded_endpoint():
        """Endpoint that should be excluded from session handling."""
        return {"excluded": True}
    
    return app


async def test_session_middleware_basic() -> None:
    """Test basic session middleware functionality."""
    print("🧪 Testing session middleware...")
    
    # Initialize database for testing
    await initialize_database()
    
    try:
        app = create_test_app()
        
        with TestClient(app) as client:
            # Test 1: First request should create a new session
            print("\n📝 Test 1: First request creates new session...")
            response = client.get("/test")
            
            assert response.status_code == 200
            data = response.json()
            assert data["has_session"] is True
            assert data["is_anonymous"] is True
            assert "session_id" in data
            assert "session_key" in data
            
            # Check that session cookie was set
            assert "salient_session" in response.cookies
            session_cookie = response.cookies["salient_session"]
            
            print(f"✅ New session created with cookie: {session_cookie[:8]}...")
            
            # Test 2: Second request with cookie should resume session
            print("\n🔄 Test 2: Second request resumes session...")
            response2 = client.get("/test", cookies={"salient_session": session_cookie})
            
            assert response2.status_code == 200
            data2 = response2.json()
            assert data2["has_session"] is True
            assert data2["session_id"] == data["session_id"]  # Same session
            
            print(f"✅ Session resumed: {data2['session_id']}")
            
            # Test 3: Request without cookie should create new session
            print("\n📝 Test 3: Request without cookie creates new session...")
            response3 = client.get("/test")  # No cookies
            
            assert response3.status_code == 200
            data3 = response3.json()
            assert data3["has_session"] is True
            assert data3["session_id"] != data["session_id"]  # Different session
            
            print(f"✅ New session created: {data3['session_id']}")
            
            print("\n🎉 Session middleware tests passed!")
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        raise
    finally:
        await shutdown_database()


async def test_session_middleware_excluded_paths() -> None:
    """Test that excluded paths don't trigger session handling."""
    print("\n🧪 Testing excluded paths...")
    
    await initialize_database()
    
    try:
        # Create app with custom excluded paths
        app = FastAPI()
        app.add_middleware(SessionMiddleware, exclude_paths=["/excluded"])
        
        @app.get("/excluded")
        async def excluded_endpoint(request: Request):
            session = get_current_session(request)
            return {"has_session": session is not None}
        
        with TestClient(app) as client:
            response = client.get("/excluded")
            assert response.status_code == 200
            data = response.json()
            assert data["has_session"] is False
            
            # No session cookie should be set
            assert "salient_session" not in response.cookies
            
            print("✅ Excluded path correctly bypassed session handling")
            
    finally:
        await shutdown_database()


if __name__ == "__main__":
    # Run the tests
    asyncio.run(test_session_middleware_basic())
    asyncio.run(test_session_middleware_excluded_paths())
