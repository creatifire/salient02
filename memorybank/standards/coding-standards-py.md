# Python Coding Standards

> Essential coding standards for maintainable, consistent Python code

## Code Style & Formatting

### PEP 8 Compliance
Follow [PEP 8](https://peps.python.org/pep-0008/) as the foundation for all Python code:

**Indentation & Whitespace:**
```python
# Use 4 spaces per indentation level (never tabs)
def example_function():
    if condition:
        do_something()
        return result
```

**Line Length:**
- **79 characters** for code
- **72 characters** for comments and docstrings
- Use parentheses for line continuation:

```python
# Good: Use parentheses for line continuation
result = some_function(
    parameter_one, parameter_two,
    parameter_three, parameter_four
)

# Good: Break before binary operators
total = (first_variable 
         + second_variable
         - third_variable)
```

**Blank Lines:**
```python
"""Module docstring."""

import os


class MyClass:
    """Class with proper spacing."""
    
    def __init__(self):
        """Constructor."""
        pass
    
    def method_one(self):
        """First method."""
        pass


def standalone_function():
    """Function separated by two blank lines."""
    pass
```

## Naming Conventions

### Variables & Functions
```python
# Use snake_case for variables and functions
user_name = "john_doe"
total_count = 42

def calculate_tax_amount(income: float) -> float:
    """Calculate tax amount based on income."""
    return income * 0.2

def send_email_notification(recipient: str) -> bool:
    """Send email notification to recipient."""
    pass
```

### Classes & Exceptions
```python
# Use PascalCase for classes
class UserManager:
    """Manages user operations."""
    pass

class DatabaseConnection:
    """Handles database connectivity."""
    pass

# Exception classes should end with 'Error'
class ValidationError(Exception):
    """Raised when validation fails."""
    pass

class ConfigurationError(Exception):
    """Raised when configuration is invalid."""
    pass
```

### Constants & Configuration
```python
# Use UPPER_CASE for constants
DEFAULT_TIMEOUT = 30
MAX_RETRY_ATTEMPTS = 3
API_BASE_URL = "https://api.example.com"

# Group related constants in classes
class DatabaseConfig:
    """Database configuration constants."""
    DEFAULT_POOL_SIZE = 20
    MAX_CONNECTIONS = 100
    TIMEOUT_SECONDS = 30
```

### Modules & Packages
```python
# Use lowercase with underscores for modules
# user_manager.py
# email_service.py
# database_utils.py

# Package structure
"""
app/
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── user.py
│   └── session.py
├── services/
│   ├── __init__.py
│   ├── auth_service.py
│   └── email_service.py
└── utils/
    ├── __init__.py
    └── validation_utils.py
"""
```

## Type Hints (Required)

### Function Signatures
```python
from typing import Dict, List, Optional, Union, Any
from decimal import Decimal

def process_user_data(
    users: List[Dict[str, str]], 
    active_only: bool = True,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """Process user data with type safety."""
    pass

def calculate_cost(
    base_amount: Decimal,
    tax_rate: float,
    discount: Optional[Decimal] = None
) -> Decimal:
    """Calculate total cost with taxes and discounts."""
    pass

# Use Union for multiple acceptable types
def format_id(user_id: Union[int, str]) -> str:
    """Format user ID as string."""
    return str(user_id)
```

### Class Type Hints
```python
from typing import ClassVar, Protocol
from dataclasses import dataclass
from datetime import datetime

@dataclass
class User:
    """User data class with type hints."""
    id: int
    name: str
    email: str
    created_at: datetime
    is_active: bool = True
    metadata: Optional[Dict[str, Any]] = None

class DatabaseProtocol(Protocol):
    """Protocol for database implementations."""
    
    def connect(self) -> bool:
        """Connect to database."""
        ...
    
    def execute(self, query: str) -> List[Dict[str, Any]]:
        """Execute database query."""
        ...

class UserService:
    """User service with typed attributes."""
    
    # Class variable type hint
    default_timeout: ClassVar[int] = 30
    
    def __init__(self, db: DatabaseProtocol) -> None:
        self.db = db
        self._cache: Dict[int, User] = {}
```

### Generic Types
```python
from typing import TypeVar, Generic, List

T = TypeVar('T')

class Repository(Generic[T]):
    """Generic repository pattern."""
    
    def __init__(self, model_class: type[T]) -> None:
        self.model_class = model_class
        self._items: List[T] = []
    
    def add(self, item: T) -> None:
        """Add item to repository."""
        self._items.append(item)
    
    def find_by_id(self, item_id: int) -> Optional[T]:
        """Find item by ID."""
        pass

# Usage
user_repo = Repository[User](User)
```

## File Organization & Module Structure

### When to Split Files

**Split into separate files when:**
- **File exceeds 500-800 lines** (excluding tests)
- **Multiple unrelated classes** in one file
- **Different responsibilities** can be clearly separated
- **Import dependencies** become circular

**Single file examples:**
```python
# Good: Single responsibility
# user_service.py - only user-related operations
# email_service.py - only email operations  
# database.py - only database connectivity
```

**Multi-file examples:**
```python
# models/ directory for related data models
# models/__init__.py
from .user import User
from .session import Session
from .message import Message

# services/ directory for business logic
# services/__init__.py  
from .user_service import UserService
from .auth_service import AuthService
```

### Module Organization Patterns

**Flat Structure (Small Projects):**
```python
project/
├── main.py
├── config.py
├── database.py
├── models.py
├── services.py
└── utils.py
```

**Layered Structure (Medium Projects):**
```python
project/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── session.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   └── auth_service.py
│   └── utils/
│       ├── __init__.py
│       └── validation.py
├── tests/
└── requirements.txt
```

### Import Organization
```python
"""Module docstring."""

# Standard library imports (alphabetical)
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Third-party imports (alphabetical)
import httpx
import sqlalchemy
from fastapi import FastAPI
from loguru import logger
from pydantic import BaseModel

# Local application imports (relative imports)
from .config import load_config
from .database import get_session
from .models import User, Session
from .services import UserService

# Avoid star imports
# from module import *  # Don't do this
```

## Class Design Best Practices

### Class Structure
```python
class UserService:
    """
    Service for managing user operations.
    
    Handles user CRUD operations, authentication, and profile management.
    Follows single responsibility principle.
    """
    
    # Class variables first
    DEFAULT_TIMEOUT: ClassVar[int] = 30
    
    def __init__(self, db_session: AsyncSession) -> None:
        """Initialize user service with database session."""
        # Public attributes
        self.db_session = db_session
        
        # Private attributes (prefix with _)
        self._cache: Dict[int, User] = {}
        self._timeout = self.DEFAULT_TIMEOUT
    
    # Properties before methods
    @property
    def cache_size(self) -> int:
        """Get current cache size."""
        return len(self._cache)
    
    # Public methods
    async def create_user(self, user_data: Dict[str, Any]) -> User:
        """Create new user with validation."""
        pass
    
    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID with caching."""
        pass
    
    # Private methods last (prefix with _)
    def _validate_user_data(self, data: Dict[str, Any]) -> bool:
        """Validate user data before creation."""
        pass
    
    def _clear_cache(self) -> None:
        """Clear user cache."""
        self._cache.clear()
```

### Inheritance & Composition
```python
# Prefer composition over inheritance
class EmailService:
    """Email service using composition."""
    
    def __init__(self, smtp_client: SMTPClient, template_engine: TemplateEngine):
        self.smtp = smtp_client
        self.templates = template_engine
    
    def send_notification(self, user: User, template: str) -> bool:
        """Send email notification."""
        pass

# Use inheritance for is-a relationships
class BaseRepository(ABC):
    """Abstract base repository."""
    
    @abstractmethod
    async def save(self, entity: Any) -> Any:
        """Save entity to storage."""
        pass

class UserRepository(BaseRepository):
    """User-specific repository implementation."""
    
    async def save(self, user: User) -> User:
        """Save user to database."""
        pass
```

### Data Classes & Models
```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import List

@dataclass
class User:
    """User data model."""
    id: int
    name: str
    email: str
    created_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Validate data after initialization."""
        if not self.email or '@' not in self.email:
            raise ValueError("Invalid email address")

# For database models, use SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    """Base class for all database models."""
    pass

class User(Base):
    """User database model."""
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
```

## Error Handling

### Exception Patterns
```python
# Custom exceptions with inheritance hierarchy
class SalientError(Exception):
    """Base exception for Salient application."""
    pass

class ValidationError(SalientError):
    """Raised when data validation fails."""
    pass

class AuthenticationError(SalientError):
    """Raised when authentication fails."""
    pass

class DatabaseError(SalientError):
    """Raised when database operations fail."""
    pass

# Exception handling with specific catches
async def process_user_request(data: Dict[str, Any]) -> User:
    """Process user request with proper error handling."""
    try:
        # Validate input data
        if not data.get('email'):
            raise ValidationError("Email is required")
        
        # Process data
        user = await create_user(data)
        return user
        
    except ValidationError:
        # Re-raise validation errors
        raise
    except DatabaseError as e:
        # Log database errors and convert to user-friendly message
        logger.error(f"Database error: {e}")
        raise SalientError("Unable to process request") from e
    except Exception as e:
        # Catch unexpected errors
        logger.exception("Unexpected error in process_user_request")
        raise SalientError("Internal server error") from e
```

## Testing Standards

### Test File Organization
```python
# tests/test_user_service.py
import pytest
from unittest.mock import Mock, AsyncMock
from app.services.user_service import UserService
from app.models import User

class TestUserService:
    """Test cases for UserService."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return AsyncMock()
    
    @pytest.fixture
    def user_service(self, mock_db_session):
        """User service instance for testing."""
        return UserService(mock_db_session)
    
    async def test_create_user_success(self, user_service):
        """Test successful user creation."""
        # Arrange
        user_data = {"name": "John Doe", "email": "john@example.com"}
        
        # Act
        result = await user_service.create_user(user_data)
        
        # Assert
        assert result.name == "John Doe"
        assert result.email == "john@example.com"
    
    async def test_create_user_validation_error(self, user_service):
        """Test user creation with invalid data."""
        # Arrange
        invalid_data = {"name": "John Doe"}  # Missing email
        
        # Act & Assert
        with pytest.raises(ValidationError, match="Email is required"):
            await user_service.create_user(invalid_data)
```

## Code Quality Tools

### Required Tools
```python
# requirements-dev.txt
black>=23.0.0           # Code formatting
ruff>=0.1.0            # Fast linting (replaces flake8, isort)
mypy>=1.7.0            # Type checking
pytest>=7.0.0          # Testing framework
pytest-asyncio>=0.21.0 # Async testing support
pytest-cov>=4.0.0      # Coverage reporting
pre-commit>=3.0.0      # Git hooks
```

### Configuration Files
```toml
# pyproject.toml
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

[tool.ruff]
line-length = 88
target-version = "py311"
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = [
    "E501",  # line too long, handled by black
    "B008",  # do not perform function calls in argument defaults
]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "--cov=app",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-fail-under=80"
]
```

## Project-Specific Standards

### For Salient Sales Bot
```python
# Database models should inherit from Base
class Session(Base):
    """Session model following project patterns."""
    __tablename__ = "sessions"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

# Services should use dependency injection
class ChatService:
    """Chat service with injected dependencies."""
    
    def __init__(
        self, 
        db_session: AsyncSession,
        llm_client: LLMClient,
        config: Dict[str, Any]
    ) -> None:
        self.db = db_session
        self.llm = llm_client
        self.config = config

# Configuration should use type hints
@dataclass
class DatabaseConfig:
    """Database configuration with validation."""
    url: str
    pool_size: int = 20
    timeout: int = 30
    
    def __post_init__(self) -> None:
        if self.pool_size <= 0:
            raise ValueError("Pool size must be positive")
```

## References

- [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [PEP 257 – Docstring Conventions](https://peps.python.org/pep-0257/)
- [PEP 484 – Type Hints](https://peps.python.org/pep-0484/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Black Code Formatter](https://black.readthedocs.io/)
- [Ruff Linter](https://docs.astral.sh/ruff/)
- [MyPy Type Checker](https://mypy.readthedocs.io/)
