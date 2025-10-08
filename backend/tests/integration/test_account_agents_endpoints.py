"""
Integration tests for multi-tenant account-agent-instance endpoints.

Tests the account_agents router functionality including:
- Router registration and availability
- Health check endpoint
- Account parameter extraction
- Error handling for invalid accounts/instances
- Session management with account/instance context
- Message persistence with agent_instance_id
- Cost tracking with account/instance attribution

Test Coverage:
- 0022-001-002-01: Router setup and health check
- 0022-001-002-02: Non-streaming chat endpoint (future)
- 0022-001-002-03: Streaming chat endpoint (future)
- 0022-001-002-04: Instance listing endpoint (future)
"""

import pytest
import pytest_asyncio
import httpx
from httpx import AsyncClient
from fastapi import FastAPI

from app.main import app
from app.database import initialize_database


# ============================================================================
# FIXTURES
# ============================================================================

@pytest_asyncio.fixture
async def client():
    """
    Create async HTTP client for testing endpoints.
    
    Initializes database before tests run to ensure proper state.
    """
    # Initialize database for integration tests
    await initialize_database()
    
    # Create ASGI transport for httpx AsyncClient
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ============================================================================
# TEST: 0022-001-002-01 - Router Setup
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_router_registered(client: AsyncClient):
    """
    Test that account_agents router is properly registered.
    
    Verifies:
    - Router is included in FastAPI app
    - Routes are accessible
    - No import errors or registration issues
    
    Test: 0022-001-002-01-01
    """
    # Test that we can access an account_agents route
    # Using health endpoint as a proxy for router registration
    response = await client.get("/accounts/test-account/agents/health")
    
    # Should get 200 OK, not 404 (which would mean router not registered)
    assert response.status_code == 200, \
        f"Router not registered - got {response.status_code}, expected 200"
    
    # Verify response structure
    data = response.json()
    assert "status" in data, "Health response missing 'status' field"
    assert "account" in data, "Health response missing 'account' field"
    assert "router" in data, "Health response missing 'router' field"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """
    Test health check endpoint functionality.
    
    Verifies:
    - Endpoint is accessible
    - Returns correct status and metadata
    - Account parameter is extracted correctly
    - Response includes endpoint documentation
    
    Test: 0022-001-002-01-02
    """
    # Test with default_account
    response = await client.get("/accounts/default_account/agents/health")
    
    assert response.status_code == 200, \
        f"Health check failed - status {response.status_code}"
    
    data = response.json()
    
    # Verify status
    assert data["status"] == "healthy", \
        f"Health status not 'healthy', got: {data.get('status')}"
    
    # Verify account parameter extraction
    assert data["account"] == "default_account", \
        f"Account parameter not extracted correctly, got: {data.get('account')}"
    
    # Verify router identification
    assert data["router"] == "account-agents", \
        f"Router identification incorrect, got: {data.get('router')}"
    
    # Verify version present
    assert "version" in data, "Version missing from health response"
    
    # Verify endpoints documentation
    assert "endpoints" in data, "Endpoints documentation missing"
    endpoints = data["endpoints"]
    
    expected_endpoints = ["health", "list", "chat", "stream"]
    for endpoint in expected_endpoints:
        assert endpoint in endpoints, \
            f"Endpoint '{endpoint}' missing from documentation"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_endpoint_different_accounts(client: AsyncClient):
    """
    Test health endpoint with different account slugs.
    
    Verifies:
    - Account parameter is dynamic and extracted correctly
    - Endpoint works for multiple accounts
    - No hardcoded account dependencies
    
    Test: 0022-001-002-01-03
    """
    test_accounts = [
        "default_account",
        "acme",
        "test-account-123",
        "another_org"
    ]
    
    for account_slug in test_accounts:
        response = await client.get(f"/accounts/{account_slug}/agents/health")
        
        assert response.status_code == 200, \
            f"Health check failed for account '{account_slug}'"
        
        data = response.json()
        assert data["account"] == account_slug, \
            f"Account parameter mismatch: expected '{account_slug}', got '{data.get('account')}'"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_router_prefix(client: AsyncClient):
    """
    Test that router prefix is correctly applied.
    
    Verifies:
    - Routes require /accounts/ prefix
    - Routes without prefix return 404
    - URL structure is enforced
    
    Test: 0022-001-002-01-04
    """
    # Try to access health without /accounts/ prefix (should fail)
    response = await client.get("/agents/health")
    
    # Should get 404, not 200 (proves /accounts/ prefix is required)
    assert response.status_code == 404, \
        f"Router prefix not enforced - /agents/health should not be accessible without /accounts/"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_response_structure(client: AsyncClient):
    """
    Test complete health response structure and types.
    
    Verifies:
    - All required fields present
    - Correct data types
    - Endpoint documentation format
    
    Test: 0022-001-002-01-05
    """
    response = await client.get("/accounts/default_account/agents/health")
    
    assert response.status_code == 200
    data = response.json()
    
    # Test required fields and types
    assert isinstance(data["status"], str), "Status should be string"
    assert isinstance(data["account"], str), "Account should be string"
    assert isinstance(data["router"], str), "Router should be string"
    assert isinstance(data["version"], str), "Version should be string"
    assert isinstance(data["endpoints"], dict), "Endpoints should be dict"
    
    # Test endpoints structure
    for endpoint_name, endpoint_path in data["endpoints"].items():
        assert isinstance(endpoint_name, str), f"Endpoint name '{endpoint_name}' should be string"
        assert isinstance(endpoint_path, str), f"Endpoint path for '{endpoint_name}' should be string"
        assert endpoint_path.startswith("GET ") or endpoint_path.startswith("POST "), \
            f"Endpoint '{endpoint_name}' should start with HTTP method"

