"""
Unit tests for SessionDependencies class parameter standardization.

Tests for CHUNK 0017-004-001-03: Update SessionDependencies class for standardized parameters
"""
"""
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
"""



import pytest
from app.agents.base.dependencies import SessionDependencies


@pytest.mark.unit
@pytest.mark.asyncio
async def test_session_dependencies_constructor():
    """
    Test that SessionDependencies constructor accepts history_limit parameter.
    
    CHUNK 0017-004-001-03 AUTOMATED-TEST 1:
    Verify constructor accepts history_limit parameter and initializes correctly.
    """
    # Test with default history_limit
    deps = await SessionDependencies.create(
        session_id="test-session-123"
    )
    
    assert hasattr(deps, 'history_limit'), "SessionDependencies should have history_limit attribute"
    assert deps.history_limit == 20, "Default history_limit should be 20"
    assert deps.session_id == "test-session-123", "Session ID should be set correctly"
    
    # Test with custom history_limit
    custom_deps = await SessionDependencies.create(
        session_id="test-session-456",
        history_limit=50
    )
    
    assert custom_deps.history_limit == 50, "Custom history_limit should be set correctly"
    assert custom_deps.session_id == "test-session-456", "Session ID should be set correctly"


@pytest.mark.unit  
@pytest.mark.asyncio
async def test_session_dependencies_no_old_params():
    """
    Test that SessionDependencies no longer accepts max_history_messages parameter.
    
    CHUNK 0017-004-001-03 AUTOMATED-TEST 2:
    Verify old parameter name max_history_messages is completely removed from interface.
    """
    # Verify the old parameter is not in the create method signature
    import inspect
    create_signature = inspect.signature(SessionDependencies.create)
    param_names = list(create_signature.parameters.keys())
    
    assert 'max_history_messages' not in param_names, \
        "Old parameter 'max_history_messages' should not be in create() method signature"
    
    assert 'history_limit' in param_names, \
        "New parameter 'history_limit' should be in create() method signature"
    
    # Verify SessionDependencies instances don't have old attribute names
    deps = await SessionDependencies.create(session_id="test-session")
    
    assert hasattr(deps, 'history_limit'), \
        "SessionDependencies should have 'history_limit' attribute"
    
    # Check that trying to access old attribute name would fail
    # (This ensures we don't accidentally leave old code paths)
    assert not hasattr(deps, 'max_history_messages'), \
        "SessionDependencies should NOT have 'max_history_messages' attribute"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_session_dependencies_method_signatures():
    """
    Test that all SessionDependencies methods use standardized parameter names.
    
    Additional test to verify all method signatures and docstrings use consistent naming.
    """
    # Verify create method docstring mentions history_limit
    create_docstring = SessionDependencies.create.__doc__
    assert 'history_limit' in create_docstring, \
        "create() method docstring should mention 'history_limit' parameter"
    
    # Verify that max_history_messages is not mentioned in docstrings  
    assert 'max_history_messages' not in create_docstring, \
        "create() method docstring should not mention old 'max_history_messages' parameter"
    
    # Test that the class can be instantiated with correct parameters
    deps = await SessionDependencies.create(
        session_id="test-docstring-session",
        user_id="test-user",
        history_limit=30
    )
    
    assert deps.history_limit == 30, "History limit should be set from parameter"
    assert deps.user_id == "test-user", "User ID should be set correctly"
    assert deps.session_id == "test-docstring-session", "Session ID should be set correctly"
