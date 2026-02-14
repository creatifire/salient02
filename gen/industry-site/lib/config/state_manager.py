"""
State management for Industry Site Generator.

Tracks progress and shares mutable state across script executions.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from datetime import datetime


class StateManager:
    """
    Manages mutable state across script executions.
    Updates site-gen-state.yaml as scripts progress.
    """
    
    def __init__(self, state_path: Path):
        """
        Initialize state manager.
        
        Args:
            state_path: Path to site-gen-state.yaml
        """
        self.state_path = Path(state_path)
        self._state: Dict[str, Any] = {}
        
    def load(self) -> Dict[str, Any]:
        """
        Load existing state or create new.
        
        Returns:
            State dictionary
        """
        if self.state_path.exists():
            with open(self.state_path) as f:
                self._state = yaml.safe_load(f) or {}
        else:
            self._state = {
                'created_at': datetime.now().isoformat(),
                'scripts_completed': [],
                'last_updated': None,
                'data': {}
            }
            self.save()
        
        return self._state
    
    def save(self) -> None:
        """Save current state to file."""
        self._state['last_updated'] = datetime.now().isoformat()
        
        # Ensure parent directory exists
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.state_path, 'w') as f:
            yaml.safe_dump(self._state, f, default_flow_style=False)
    
    def mark_script_complete(self, script_name: str) -> None:
        """
        Mark a script as completed.
        
        Args:
            script_name: Name of completed script (e.g., '01_init_config')
        """
        if script_name not in self._state['scripts_completed']:
            self._state['scripts_completed'].append(script_name)
        self.save()
    
    def is_script_complete(self, script_name: str) -> bool:
        """
        Check if script has been completed.
        
        Args:
            script_name: Name of script to check
            
        Returns:
            True if script completed
        """
        return script_name in self._state.get('scripts_completed', [])
    
    def set(self, key: str, value: Any) -> None:
        """
        Set state value.
        
        Args:
            key: State key
            value: Value to store
        """
        if 'data' not in self._state:
            self._state['data'] = {}
        
        self._state['data'][key] = value
        self.save()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get state value.
        
        Args:
            key: State key
            default: Default if key not found
            
        Returns:
            State value or default
        """
        return self._state.get('data', {}).get(key, default)
    
    def update(self, updates: Dict[str, Any]) -> None:
        """
        Update multiple state values.
        
        Args:
            updates: Dictionary of key-value pairs to update
        """
        if 'data' not in self._state:
            self._state['data'] = {}
        
        self._state['data'].update(updates)
        self.save()
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all state data.
        
        Returns:
            Dictionary of all state data
        """
        return self._state.get('data', {})
    
    def get_completed_scripts(self) -> list:
        """
        Get list of completed scripts.
        
        Returns:
            List of completed script names
        """
        return self._state.get('scripts_completed', [])
    
    def reset(self) -> None:
        """
        Reset state to initial values.
        Preserves created_at timestamp.
        """
        created_at = self._state.get('created_at', datetime.now().isoformat())
        self._state = {
            'created_at': created_at,
            'scripts_completed': [],
            'last_updated': None,
            'data': {}
        }
        self.save()
    
    @property
    def created_at(self) -> Optional[str]:
        """Get state creation timestamp."""
        return self._state.get('created_at')
    
    @property
    def last_updated(self) -> Optional[str]:
        """Get last update timestamp."""
        return self._state.get('last_updated')
