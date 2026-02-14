"""
Logging integration for Industry Site Generator.
Leverages the backend's Logfire implementation.
"""

import sys
from pathlib import Path

# Add backend to path to leverage existing logger
backend_path = Path(__file__).parent.parent.parent.parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

try:
    import logfire
    
    def get_logger(name: str):
        """
        Get logger instance using backend's logfire.
        
        Args:
            name: Logger name (typically __name__)
            
        Returns:
            Logfire instance for structured logging
        """
        return logfire
        
except ImportError:
    # Fallback to standard logging if logfire not available
    import logging
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    def get_logger(name: str):
        """
        Get standard logger as fallback.
        
        Args:
            name: Logger name (typically __name__)
            
        Returns:
            Standard Python logger instance
        """
        return logging.getLogger(name)
