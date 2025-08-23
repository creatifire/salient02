# Code Commenting Best Practices

> Guidelines for writing clear, maintainable comments in Python, JavaScript, and TypeScript

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

## JavaScript/TypeScript Commenting Standards

### Single-Line Comments
For brief explanations and clarifications:

```javascript
// Debounce user input to avoid excessive API calls
const debouncedSearch = debounce(handleSearch, 300);

// Convert to display timezone for user's locale
const localTime = utcTime.toLocaleString(userTimezone);
```

### Block Comments
For longer explanations or algorithm descriptions:

```javascript
/*
 * Calculate the optimal layout for responsive grid items.
 * 
 * This algorithm considers:
 * - Available container width
 * - Minimum item width requirements  
 * - Preferred aspect ratios
 * - Screen density for crisp rendering
 * 
 * Returns layout with item dimensions and positions.
 */
function calculateGridLayout(containerWidth, items) {
    // Implementation
}
```

### JSDoc Documentation
Standard for function and class documentation:

```typescript
/**
 * Manages user session state and authentication.
 * 
 * Handles token refresh, logout, and session persistence
 * across browser tabs using localStorage and events.
 * 
 * @example
 * ```typescript
 * const session = new SessionManager();
 * await session.login(credentials);
 * ```
 */
class SessionManager {
    /**
     * Authenticate user with email and password.
     * 
     * @param credentials - User login information
     * @param credentials.email - User's email address
     * @param credentials.password - User's password  
     * @param rememberMe - Whether to persist session across browser restarts
     * @returns Promise resolving to user profile data
     * @throws {AuthenticationError} When credentials are invalid
     * @throws {NetworkError} When API is unreachable
     */
    async login(
        credentials: { email: string; password: string },
        rememberMe: boolean = false
    ): Promise<UserProfile> {
        // Implementation
    }
}
```

**JSDoc Tags:**
- `@param` - Parameter descriptions
- `@returns` - Return value description
- `@throws` - Exceptions that may be thrown
- `@example` - Usage examples
- `@deprecated` - Mark deprecated functions
- `@since` - Version when feature was added
- `@see` - References to related functions/docs

### TypeScript-Specific Comments
Leverage type system with strategic comments:

```typescript
interface ApiResponse<T> {
    data: T;
    status: 'success' | 'error';
    // Include message for error cases and optional success metadata
    message?: string;
}

// Type assertion needed here due to third-party library limitations
const config = (window as any).APP_CONFIG as AppConfig;

// Exhaustive switch ensures all enum values are handled
function handleUserRole(role: UserRole): string {
    switch (role) {
        case UserRole.ADMIN:
            return 'Administrator';
        case UserRole.USER:
            return 'Standard User';
        default:
            // TypeScript will error if we miss a case
            const _exhaustive: never = role;
            throw new Error(`Unhandled role: ${role}`);
    }
}
```

### Component Documentation (React/Astro)
Document component interfaces and usage:

```typescript
/**
 * Chat widget for customer support integration.
 * 
 * Provides floating chat interface that can be embedded
 * on any page via script tag or component import.
 * 
 * @param backendUrl - Base URL for chat API (default: same origin)
 * @param theme - Visual theme configuration
 * @param position - Widget position on screen
 * @param initialMessage - Pre-populate chat with message
 */
interface ChatWidgetProps {
    backendUrl?: string;
    theme?: 'light' | 'dark' | 'auto';
    position?: 'bottom-right' | 'bottom-left';
    initialMessage?: string;
}

export function ChatWidget({ 
    backendUrl = '', 
    theme = 'auto',
    position = 'bottom-right',
    initialMessage 
}: ChatWidgetProps) {
    // Implementation with inline comments for complex logic
}
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
- **API Endpoints**: Use JSDoc for request/response formats
- **LLM Integration**: Comment prompt engineering decisions and model parameters
- **Security**: Document authentication flows and data handling

### Example Project Application
```python
# Backend example (app/models/session.py)
class Session(Base):
    """User session for chat persistence and resumption.
    
    Sessions are automatically created on first chat interaction and
    persist across browser sessions via HTTP-only cookies. This enables
    conversation continuity without requiring user registration.
    
    The session_key serves as the primary identifier and must be
    cryptographically secure to prevent session hijacking.
    """
    
    session_key: Mapped[str] = mapped_column(
        String(64), 
        unique=True, 
        index=True,
        # Use URL-safe base64 encoding for session keys
        comment="Cryptographically secure session identifier"
    )
```

```typescript
// Frontend example (web/src/components/ChatWidget.ts)
/**
 * Initialize chat widget with security considerations.
 * 
 * Same-origin policy enforced by default to prevent CSRF.
 * Cross-origin requests require explicit configuration.
 */
function initializeWidget(config: WidgetConfig): void {
    // Validate backend URL to prevent injection attacks
    const backendUrl = sanitizeUrl(config.backendUrl || window.location.origin);
    
    // Use fetch with credentials for session cookie support
    const fetchOptions: RequestInit = {
        credentials: 'same-origin',  // Include session cookies
        headers: {
            'Content-Type': 'application/json',
            // CSRF protection via custom header
            'X-Requested-With': 'XMLHttpRequest'
        }
    };
}
```

## Tools and Automation

### Python
- **Linting**: Use `pylint`, `flake8` for comment quality checks
- **Documentation**: Use Sphinx with autodoc for docstring generation
- **Type Checking**: mypy helps reduce need for type-related comments

### JavaScript/TypeScript
- **Linting**: ESLint rules for comment quality and JSDoc validation
- **Documentation**: TypeDoc for automatic API documentation
- **Type Checking**: TypeScript reduces need for type-related comments

### Project Integration
- **Pre-commit hooks**: Validate comment formatting and completeness
- **Code review**: Include comment quality in review criteria
- **Documentation site**: Auto-generate docs from docstrings/JSDoc

## References

- [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [PEP 257 – Docstring Conventions](https://peps.python.org/pep-0257/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [JSDoc Documentation](https://jsdoc.app/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Clean Code by Robert Martin](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)
