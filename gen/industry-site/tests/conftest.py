"""
Shared pytest configuration and fixtures for Industry Site Generator tests.
"""

import sys
from pathlib import Path

# Add the project root (parent of tests/) to Python path so tests can import lib modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
