"""Configuration loader with environment variable substitution."""

from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from dotenv import load_dotenv
import os
from .validator import validate_config
from ..errors.exceptions import ConfigValidationError


class ConfigLoader:
    """
    Loads and validates site-gen-config.yaml with environment variable substitution.
    Config is immutable after loading.
    """
    
    def __init__(self, config_path: Path, env_file: Optional[Path] = None):
        """
        Initialize config loader.
        
        Args:
            config_path: Path to site-gen-config.yaml
            env_file: Optional path to .env file (defaults to project root)
        """
        self.config_path = Path(config_path)
        
        # Default to project root .env (5 levels up: config_loader.py -> config/ -> lib/ -> industry-site/ -> gen/ -> salient02/)
        if env_file is None:
            self.env_file = Path(__file__).parent.parent.parent.parent.parent / '.env'
        else:
            self.env_file = Path(env_file)
        
        self._config: Optional[Dict[str, Any]] = None
        
    def load(self) -> Dict[str, Any]:
        """
        Load and validate configuration.
        
        Returns:
            Validated config dictionary
            
        Raises:
            ConfigValidationError: If config is invalid
            FileNotFoundError: If config file doesn't exist
        """
        # Load environment variables from .env file
        if self.env_file.exists():
            load_dotenv(self.env_file)
        
        # Check if config file exists
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        # Read YAML
        with open(self.config_path, 'r', encoding='utf-8') as f:
            raw_config = yaml.safe_load(f)
        
        if raw_config is None:
            raise ConfigValidationError("Config file is empty")
        
        # Substitute environment variables
        config = self._substitute_env_vars(raw_config)
        
        # Validate
        validate_config(config)
        
        self._config = config
        return config
    
    def _substitute_env_vars(self, obj: Any) -> Any:
        """
        Recursively substitute ${VAR_NAME} with environment variables.
        
        Args:
            obj: YAML object (dict, list, str, etc.)
            
        Returns:
            Object with environment variables substituted
        """
        if isinstance(obj, dict):
            return {k: self._substitute_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_env_vars(item) for item in obj]
        elif isinstance(obj, str) and obj.startswith('${') and obj.endswith('}'):
            var_name = obj[2:-1]
            # Return environment variable value or original string if not found
            return os.getenv(var_name, obj)
        else:
            return obj
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get config value using dot notation.
        
        Args:
            key_path: Dot-separated path (e.g., 'llm.models.tool_calling')
            default: Default value if key not found
            
        Returns:
            Config value or default
            
        Example:
            >>> config = ConfigLoader('config.yaml')
            >>> config.load()
            >>> config.get('company.name')
            'AgriTech Solutions'
        """
        if self._config is None:
            raise RuntimeError("Config not loaded. Call load() first.")
        
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    @property
    def config(self) -> Dict[str, Any]:
        """
        Get the full config dictionary.
        
        Returns:
            Complete configuration dictionary
            
        Raises:
            RuntimeError: If config not loaded yet
        """
        if self._config is None:
            raise RuntimeError("Config not loaded. Call load() first.")
        return self._config
    
    @property
    def company(self) -> Dict[str, str]:
        """
        Get company section.
        
        Returns:
            Company configuration dictionary
        """
        return self.get('company', {})
    
    @property
    def llm(self) -> Dict[str, Any]:
        """
        Get LLM configuration.
        
        Returns:
            LLM configuration dictionary
        """
        return self.get('llm', {})
    
    @property
    def generation(self) -> Dict[str, Any]:
        """
        Get generation parameters.
        
        Returns:
            Generation parameters dictionary
        """
        return self.get('generation', {})
    
    def __getitem__(self, key: str) -> Any:
        """
        Allow dictionary-style access to config.
        
        Args:
            key: Top-level config key
            
        Returns:
            Config value
        """
        if self._config is None:
            raise RuntimeError("Config not loaded. Call load() first.")
        return self._config[key]
    
    def __contains__(self, key: str) -> bool:
        """
        Check if key exists in config.
        
        Args:
            key: Top-level config key
            
        Returns:
            True if key exists
        """
        if self._config is None:
            raise RuntimeError("Config not loaded. Call load() first.")
        return key in self._config
