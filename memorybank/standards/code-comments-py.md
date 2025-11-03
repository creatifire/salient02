<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Python Code Commenting Best Practices

> Guidelines for writing clear, maintainable comments in Python code

## Philosophy

Good comments enhance code readability and maintainability by explaining the reasoning behind implementation decisions, not just describing what the code does. Well-written code should be self-explanatory in terms of its functionality, while comments provide context about intent, constraints, and decisions.

## General Principles

### 🎯 **Focus on "Why", Not "What"**
- Explain the reasoning behind code decisions
- Describe non-obvious implementation choices
- Document business rules and constraints
- Avoid restating what the code obviously does

### 📝 **Keep Comments Concise and Relevant**
- Use clear, direct language
- Be specific and actionable
- Avoid unnecessary jargon
- Make every comment count

### 🔄 **Maintain Currency**
- Update comments when code changes
- Remove obsolete comments immediately
- Treat comments as part of the codebase requiring maintenance
- Outdated comments are worse than no comments

### 🚫 **Avoid Redundancy**
- Don't comment self-explanatory code
- Focus on complex or non-obvious sections
- Let the code speak for itself when it's clear

## Python Commenting Standards

### Block Comments
Use for explaining sections of code, algorithms, or complex logic:

```python
# Calculate compound interest using the formula: A = P(1 + r/n)^(nt)
# This approach handles edge cases for daily compounding and leap years
# to ensure accuracy for financial calculations
principal = 1000
rate = 0.05
compounds_per_year = 365
years = 10
```

**Guidelines:**
- Indent to match the code level
- Start each line with `#` followed by one space
- Use blank lines to separate comment blocks
- Keep lines ≤ 72 characters for readability

### Inline Comments
Use sparingly for clarifying specific statements:

```python
timeout = 30  # API timeout in seconds, matches service SLA
x = y * 2 + 1  # Transform to display coordinates
```

**Guidelines:**
- Separate from code with at least two spaces
- Use only when the purpose isn't obvious
- Avoid for simple variable assignments

### Docstrings (PEP 257)
Document all public modules, functions, classes, and methods:

```python
def calculate_tax(income: float, filing_status: str) -> float:
    """Calculate federal income tax based on 2024 tax brackets.
    
    Uses the standard deduction and tax brackets for the given filing
    status. Does not include state taxes or other deductions.
    
    Args:
        income: Gross annual income in USD
        filing_status: One of 'single', 'married_joint', 'married_separate', 'head_of_household'
        
    Returns:
        Federal tax owed in USD
        
    Raises:
        ValueError: If filing_status is not recognized
        
    Example:
        >>> calculate_tax(50000, 'single')
        5147.50
    """
    # Implementation here
```

**Docstring Styles:**
- **Google Style**: Used above, clear and readable
- **NumPy Style**: Good for scientific computing
- **Sphinx Style**: Traditional rST format

**Required Elements:**
- Brief description (one line)
- Detailed explanation (if needed)
- Args/Parameters
- Returns/Yields
- Raises/Exceptions
- Examples (for complex functions)

### Type Hints and Comments
Combine type hints with strategic comments:

```python
from typing import Dict, List, Optional

def process_user_data(
    users: List[Dict[str, str]], 
    active_only: bool = True
) -> Optional[Dict[str, int]]:
    """Process user data and return engagement metrics.
    
    Filters users based on activity status and calculates key metrics
    used for the monthly engagement report.
    """
    # Filter logic handles edge case where last_login might be null
    if active_only:
        # Users with login in last 30 days considered active
        active_users = [u for u in users if u.get('last_login')]
        return calculate_engagement(active_users)
    
    return calculate_engagement(users)
```

### TODO and FIXME Comments
Mark technical debt and future improvements:

```python
# TODO: Implement caching for expensive calculations (Issue #123)
# FIXME: Race condition possible with concurrent requests
# NOTE: This workaround handles legacy API format until v2 migration
# WARNING: Performance degrades with >1000 items, needs optimization
```

### Module-Level Documentation
Every Python module should have a comprehensive docstring:

```python
"""
Configuration management for the Salient Sales Bot backend.

This module provides centralized configuration loading from YAML files and
environment variables, with validation, defaults, and security-first design.

Key Features:
- YAML configuration with environment variable overrides
- Security-enforced environment variables for sensitive data
- Configuration caching for performance
- Comprehensive validation with sensible defaults
- Support for development, staging, and production environments

Usage:
    config = load_config()
    db_url = get_database_url()
    session_config = get_session_config()
"""
```

### Class Documentation
Document classes with their purpose, key attributes, and usage patterns:

```python
class DatabaseService:
    """
    Async database service with connection pooling and session management.
    
    Provides:
    - Async engine with connection pooling
    - Session factory for creating async sessions
    - Health check capabilities
    - Graceful startup/shutdown
    
    Attributes:
        _engine: SQLAlchemy async engine instance
        _session_factory: Async session maker
        _is_initialized: Service initialization status
        
    Example:
        >>> service = DatabaseService()
        >>> await service.initialize()
        >>> async with service.get_session() as session:
        ...     result = await session.execute(query)
    """
```

### Database Model Documentation
Document SQLAlchemy models with business context:

```python
class Session(Base):
    """
    User session for chat persistence and resumption.
    
    Sessions are automatically created on first chat interaction and
    persist across browser sessions via HTTP-only cookies. This enables
    conversation continuity without requiring user registration.
    
    The session_key serves as the primary identifier and must be
    cryptographically secure to prevent session hijacking.
    
    Relationships:
    - messages: One-to-many chat message history
    - llm_requests: One-to-many LLM API call tracking
    - profile: One-to-one customer profile data
    """
    
    session_key: Mapped[str] = mapped_column(
        String(64), 
        unique=True, 
        index=True,
        # Use URL-safe base64 encoding for session keys
        comment="Cryptographically secure session identifier"
    )
```

## Comment Anti-Patterns

### ❌ **Don't Do This**
```python
# Bad: Obvious and redundant
i = i + 1  # Increment i by 1

# Bad: Outdated information
# TODO: Add error handling (this was done months ago)

# Bad: Explaining what instead of why
# Loop through users
for user in users:
    # Check if user is active
    if user.active:
        # Send email
        send_email(user)
```

### ✅ **Do This Instead**
```python
# Good: Explains business context
i += 1  # Move to next page in paginated results

# Good: Current and actionable
# TODO: Add retry logic for transient API failures (Issue #456)

# Good: Explains why and provides context
# Send engagement emails only to users who opted in during the last 30 days
for user in recently_active_users:
    if user.marketing_consent and user.last_login > thirty_days_ago:
        send_engagement_email(user)
```

## Project-Specific Guidelines

### For Salient Sales Bot
- **Configuration**: Comment config keys and their business impact
- **Database Models**: Document relationships and constraints in docstrings
- **API Endpoints**: Document request/response formats and error cases
- **LLM Integration**: Comment prompt engineering decisions and model parameters
- **Security**: Document authentication flows and data handling

### Security-Focused Comments
```python
# Database configuration with security-enforced environment variables
# Database URL must come from environment for security (never in YAML)
db_cfg = config.setdefault("database", {})
env_database_url = get_env("DATABASE_URL")
if not env_database_url:
    raise ValueError(
        "DATABASE_URL environment variable is required. "
        "Example: DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dbname"
    )
```

### Performance Comments
```python
# Global configuration cache to avoid repeated YAML parsing
_CONFIG_CACHE: Dict[str, Any] | None = None

def load_config() -> Dict[str, Any]:
    """Load and validate application configuration from YAML and environment."""
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE  # Return cached config for performance
```

## Tools and Automation

### Python Tools
- **Linting**: Use `pylint`, `flake8` for comment quality checks
- **Documentation**: Use Sphinx with autodoc for docstring generation
- **Type Checking**: mypy helps reduce need for type-related comments
- **Docstring validation**: pydocstyle for PEP 257 compliance

### IDE Integration
- **VS Code**: Python Docstring Generator extension
- **PyCharm**: Built-in docstring generation and validation
- **Vim/Neovim**: vim-python-pep8-indent for proper comment formatting

### Pre-commit Hooks
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/pydocstyle
    rev: 6.1.1
    hooks:
      - id: pydocstyle
        args: [--convention=google]
```

## References

- [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [PEP 257 – Docstring Conventions](https://peps.python.org/pep-0257/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [NumPy Docstring Standard](https://numpydoc.readthedocs.io/en/latest/format.html)
- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [Clean Code by Robert Martin](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)
