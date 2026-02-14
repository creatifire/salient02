"""
Unit tests for StateManager class.
"""

import pytest
from pathlib import Path
from datetime import datetime
from lib.config.state_manager import StateManager


@pytest.fixture
def temp_state_file(tmp_path):
    """Create a temporary state file path."""
    return tmp_path / "test-state.yaml"


@pytest.fixture
def state_manager(temp_state_file):
    """Create a StateManager instance with temporary file."""
    return StateManager(temp_state_file)


@pytest.mark.unit
def test_creates_new_state_file(state_manager, temp_state_file):
    """Test that StateManager creates a new state file if missing."""
    # Initially file should not exist
    assert not temp_state_file.exists()
    
    # Load creates the file
    state_manager.load()
    
    # Verify file was created
    assert temp_state_file.exists()
    
    # Verify initial structure
    state = state_manager._state
    assert 'created_at' in state
    assert 'scripts_completed' in state
    assert 'last_updated' in state
    assert 'data' in state
    assert state['scripts_completed'] == []
    assert state['data'] == {}


@pytest.mark.unit
def test_loads_existing_state(state_manager, temp_state_file):
    """Test that StateManager loads existing state correctly."""
    # Create initial state
    state_manager.load()
    state_manager.set('test_key', 'test_value')
    state_manager.mark_script_complete('script_01')
    
    # Create new StateManager instance
    new_state_manager = StateManager(temp_state_file)
    new_state_manager.load()
    
    # Verify loaded state
    assert new_state_manager.get('test_key') == 'test_value'
    assert new_state_manager.is_script_complete('script_01')


@pytest.mark.unit
def test_set_and_get_values(state_manager):
    """Test storing and retrieving state values."""
    state_manager.load()
    
    # Set single values
    state_manager.set('key1', 'value1')
    state_manager.set('key2', 42)
    state_manager.set('key3', {'nested': 'dict'})
    
    # Verify values
    assert state_manager.get('key1') == 'value1'
    assert state_manager.get('key2') == 42
    assert state_manager.get('key3') == {'nested': 'dict'}
    
    # Test default values
    assert state_manager.get('nonexistent') is None
    assert state_manager.get('nonexistent', 'default') == 'default'


@pytest.mark.unit
def test_update_multiple_values(state_manager):
    """Test updating multiple state values at once."""
    state_manager.load()
    
    # Update multiple values
    updates = {
        'product_count': 100,
        'industry': 'AgTech',
        'status': 'in_progress'
    }
    state_manager.update(updates)
    
    # Verify all values
    assert state_manager.get('product_count') == 100
    assert state_manager.get('industry') == 'AgTech'
    assert state_manager.get('status') == 'in_progress'


@pytest.mark.unit
def test_get_all(state_manager):
    """Test retrieving all state data."""
    state_manager.load()
    
    # Set multiple values
    state_manager.set('key1', 'value1')
    state_manager.set('key2', 'value2')
    
    # Get all data
    all_data = state_manager.get_all()
    
    assert all_data == {'key1': 'value1', 'key2': 'value2'}


@pytest.mark.unit
def test_mark_script_complete(state_manager):
    """Test marking scripts as complete."""
    state_manager.load()
    
    # Mark scripts complete
    state_manager.mark_script_complete('01_init_config')
    state_manager.mark_script_complete('02_research_industry')
    
    # Verify completion tracking
    assert state_manager.is_script_complete('01_init_config')
    assert state_manager.is_script_complete('02_research_industry')
    assert not state_manager.is_script_complete('03_generate_products')
    
    # Verify completed scripts list
    completed = state_manager.get_completed_scripts()
    assert '01_init_config' in completed
    assert '02_research_industry' in completed
    assert len(completed) == 2


@pytest.mark.unit
def test_mark_script_complete_idempotent(state_manager):
    """Test that marking script complete multiple times doesn't duplicate."""
    state_manager.load()
    
    # Mark same script multiple times
    state_manager.mark_script_complete('test_script')
    state_manager.mark_script_complete('test_script')
    state_manager.mark_script_complete('test_script')
    
    # Should only appear once
    completed = state_manager.get_completed_scripts()
    assert completed.count('test_script') == 1


@pytest.mark.unit
def test_is_script_complete(state_manager):
    """Test checking script completion status."""
    state_manager.load()
    
    # Initially nothing is complete
    assert not state_manager.is_script_complete('test_script')
    
    # Mark complete
    state_manager.mark_script_complete('test_script')
    
    # Now it should be complete
    assert state_manager.is_script_complete('test_script')


@pytest.mark.unit
def test_timestamps_updated(state_manager):
    """Test that timestamps are updated on save."""
    state_manager.load()
    
    # Check created_at exists
    assert state_manager.created_at is not None
    created_at = state_manager.created_at
    
    # Initially last_updated might be None or set
    initial_last_updated = state_manager.last_updated
    
    # Make a change
    state_manager.set('test_key', 'test_value')
    
    # Verify last_updated was set
    assert state_manager.last_updated is not None
    assert state_manager.last_updated != initial_last_updated
    
    # created_at should not change
    assert state_manager.created_at == created_at


@pytest.mark.unit
def test_timestamps_are_iso_format(state_manager):
    """Test that timestamps are in ISO format."""
    state_manager.load()
    
    # Verify timestamps can be parsed
    created_at = state_manager.created_at
    assert created_at is not None
    
    # Should be parseable as ISO format
    datetime.fromisoformat(created_at)
    
    # Set a value to trigger save
    state_manager.set('test', 'value')
    
    # Verify last_updated is also ISO format
    last_updated = state_manager.last_updated
    assert last_updated is not None
    datetime.fromisoformat(last_updated)


@pytest.mark.unit
def test_reset_state(state_manager):
    """Test resetting state to initial values."""
    state_manager.load()
    original_created_at = state_manager.created_at
    
    # Add some data
    state_manager.set('key1', 'value1')
    state_manager.mark_script_complete('script_01')
    
    # Reset
    state_manager.reset()
    
    # Verify state is cleared
    assert state_manager.get_all() == {}
    assert state_manager.get_completed_scripts() == []
    
    # created_at should be preserved
    assert state_manager.created_at == original_created_at


@pytest.mark.unit
def test_state_persists_across_instances(temp_state_file):
    """Test that state persists when loading with new instances."""
    # First instance
    state1 = StateManager(temp_state_file)
    state1.load()
    state1.set('persistent_key', 'persistent_value')
    state1.mark_script_complete('script_01')
    
    # Second instance
    state2 = StateManager(temp_state_file)
    state2.load()
    
    # Verify persistence
    assert state2.get('persistent_key') == 'persistent_value'
    assert state2.is_script_complete('script_01')
    
    # Verify created_at is the same
    assert state1.created_at == state2.created_at
