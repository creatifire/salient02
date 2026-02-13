# Industry Site Generator - Code Organization

## Overview

Hybrid architecture using classes for stateful components (LLM clients, config, state) and pure functions for utilities (validation, transformation, I/O). Code organized by function in `lib/` folder to maximize reuse across scripts.

## Core Principles

1. **Immutable Config**: `site-gen-config.yaml` created by Script 1, read-only for all subsequent scripts
2. **Mutable State**: `site-gen-state.yaml` tracks progress, updated by each script
3. **External Prompts**: Prompts stored as markdown files in `lib/llm/prompts/`
4. **Function-Based Organization**: `lib/` organized by functional domain
5. **Centralized Error Handling**: Shared exceptions, retry logic, logging
6. **Environment Integration**: Reads from project `.env` file
7. **Manual Testing**: Code structured for clarity and debuggability

## Directory Structure

```
gen/industry-site/
├── lib/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── config_loader.py      # ConfigLoader class
│   │   ├── state_manager.py      # StateManager class
│   │   └── validator.py          # Config validation functions
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py              # LLMClient class
│   │   ├── retry.py               # Retry logic with backoff
│   │   └── prompts/               # External prompt files
│   │       ├── __init__.py
│   │       ├── loader.py          # Prompt loader utility
│   │       ├── research/          # Research prompts (.md)
│   │       │   ├── search_companies.md
│   │       │   ├── analyze_website.md
│   │       │   ├── extract_products.md
│   │       │   └── categorize_products.md
│   │       ├── generation/        # Generation prompts (.md)
│   │       │   ├── product_names.md
│   │       │   ├── product_page.md
│   │       │   ├── category_page.md
│   │       │   ├── home_page.md
│   │       │   ├── directory_entries.md
│   │       │   └── new_schema.md
│   │       ├── analysis/          # Analysis prompts (.md)
│   │       │   ├── schema_relevance.md
│   │       │   └── propose_schemas.md
│   │       ├── validation/        # Validation prompts (.md)
│   │       │   └── demo_features.md
│   │       └── system/            # System prompts (.md)
│   │           ├── researcher.md
│   │           ├── generator.md
│   │           └── analyst.md
│   ├── research/
│   │   ├── __init__.py
│   │   ├── exa_client.py          # Exa search integration
│   │   ├── jina_reader.py         # Jina Reader scraping
│   │   └── analyzer.py            # Research analysis functions
│   ├── generation/
│   │   ├── __init__.py
│   │   ├── product_generator.py   # Product generation functions
│   │   ├── directory_generator.py # Generic directory CSV generator
│   │   ├── page_generator.py      # Markdown page generation
│   │   └── schema_generator.py    # New schema creation
│   ├── validation/
│   │   ├── __init__.py
│   │   ├── schema_validator.py    # Validate CSVs against schemas
│   │   ├── link_validator.py      # Check internal links
│   │   ├── data_validator.py      # Check data consistency
│   │   └── relationship_validator.py # Validate relationships
│   ├── io/
│   │   ├── __init__.py
│   │   ├── file_ops.py            # File read/write utilities
│   │   ├── csv_ops.py             # CSV operations
│   │   ├── yaml_ops.py            # YAML operations
│   │   └── markdown_ops.py        # Markdown parsing/generation
│   ├── errors/
│   │   ├── __init__.py
│   │   ├── exceptions.py          # Custom exception types
│   │   └── handlers.py            # Error handling utilities
│   └── logging/
│       ├── __init__.py
│       └── logger.py              # Leverage backend logger
├── 01_init_config.py
├── 02_research_industry.py
├── 03_generate_product_schema.py
├── 04_analyze_schemas.py
├── 05_create_schemas.py
├── 06_generate_directories.py
├── 07_generate_product_pages.py
├── 08_generate_category_pages.py
├── 09_generate_site_pages.py
├── 10_validate_site.py
├── 11_convert_to_astro.py
└── 12_generate_demo_features.py
```

## Core Classes

### ConfigLoader

**Purpose**: Load and validate immutable configuration

**File**: `lib/config/config_loader.py`

```python
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from dotenv import load_dotenv
import os
from .validator import validate_config

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
        self.config_path = config_path
        self.env_file = env_file or Path(__file__).parent.parent.parent.parent / '.env'
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
        # Load environment variables
        load_dotenv(self.env_file)
        
        # Read YAML
        with open(self.config_path) as f:
            raw_config = yaml.safe_load(f)
        
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
    def company(self) -> Dict[str, str]:
        """Get company section."""
        return self.get('company', {})
    
    @property
    def llm(self) -> Dict[str, Any]:
        """Get LLM configuration."""
        return self.get('llm', {})
    
    @property
    def generation(self) -> Dict[str, Any]:
        """Get generation parameters."""
        return self.get('generation', {})
```

---

### StateManager

**Purpose**: Track progress and share mutable state across scripts

**File**: `lib/config/state_manager.py`

```python
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
        self.state_path = state_path
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
        """Get all state data."""
        return self._state.get('data', {})
```

---

### LLMClient

**Purpose**: Unified LLM interaction with retry logic

**File**: `lib/llm/client.py`

```python
from openai import OpenAI
from typing import List, Dict, Any, Optional, Callable
import time
from ..errors.exceptions import LLMError, LLMRetryExhausted
from ..logging.logger import get_logger
from .retry import exponential_backoff

logger = get_logger(__name__)

class LLMClient:
    """
    Unified LLM client with retry logic and logging.
    Supports both tool calling and text generation models.
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://openrouter.ai/api/v1",
        default_model: Optional[str] = None,
        max_retries: int = 3,
        timeout: int = 60
    ):
        """
        Initialize LLM client.
        
        Args:
            api_key: OpenRouter API key
            base_url: API base URL
            default_model: Default model to use
            max_retries: Maximum retry attempts
            timeout: Request timeout in seconds
        """
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout
        )
        self.default_model = default_model
        self.max_retries = max_retries
        self.call_count = 0
        
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Make chat completion request with retry logic.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (overrides default)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            tools: Tool definitions for function calling
            tool_choice: Tool selection strategy
            
        Returns:
            Response dictionary with 'content', 'tool_calls', 'usage'
            
        Raises:
            LLMRetryExhausted: If all retries failed
            LLMError: For other API errors
            
        Example:
            >>> response = client.chat([
            ...     {"role": "system", "content": "You are helpful."},
            ...     {"role": "user", "content": "Hello!"}
            ... ])
            >>> print(response['content'])
        """
        model = model or self.default_model
        if not model:
            raise ValueError("No model specified and no default set")
        
        self.call_count += 1
        
        logger.info(
            'llm_call_start',
            call_number=self.call_count,
            model=model,
            message_count=len(messages),
            has_tools=tools is not None
        )
        
        @exponential_backoff(max_retries=self.max_retries)
        def _make_request():
            return self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
                tool_choice=tool_choice
            )
        
        try:
            response = _make_request()
            
            result = {
                'content': response.choices[0].message.content,
                'tool_calls': None,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                },
                'model': response.model,
                'finish_reason': response.choices[0].finish_reason
            }
            
            # Handle tool calls
            if response.choices[0].message.tool_calls:
                result['tool_calls'] = [
                    {
                        'id': tc.id,
                        'function': tc.function.name,
                        'arguments': tc.function.arguments
                    }
                    for tc in response.choices[0].message.tool_calls
                ]
            
            logger.info(
                'llm_call_success',
                call_number=self.call_count,
                tokens=result['usage']['total_tokens'],
                finish_reason=result['finish_reason']
            )
            
            return result
            
        except Exception as e:
            logger.error(
                'llm_call_failed',
                call_number=self.call_count,
                error=str(e)
            )
            raise LLMError(f"LLM call failed: {str(e)}") from e
    
    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate text from prompt (convenience method).
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            model: Model to use
            **kwargs: Additional arguments to chat()
            
        Returns:
            Generated text content
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self.chat(messages, model=model, **kwargs)
        return response['content']
```

---

### Retry Logic

**File**: `lib/llm/retry.py`

```python
from functools import wraps
import time
from typing import Callable, Any
from ..errors.exceptions import LLMRetryExhausted
from ..logging.logger import get_logger

logger = get_logger(__name__)

def exponential_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0
) -> Callable:
    """
    Decorator for exponential backoff retry logic.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential growth
        
    Returns:
        Decorated function with retry logic
        
    Example:
        >>> @exponential_backoff(max_retries=3)
        ... def api_call():
        ...     return requests.get('https://api.example.com')
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(
                            'retry_exhausted',
                            function=func.__name__,
                            attempts=attempt + 1,
                            error=str(e)
                        )
                        raise LLMRetryExhausted(
                            f"Failed after {max_retries + 1} attempts: {str(e)}"
                        ) from e
                    
                    # Calculate delay
                    delay = min(
                        base_delay * (exponential_base ** attempt),
                        max_delay
                    )
                    
                    logger.warning(
                        'retry_attempt',
                        function=func.__name__,
                        attempt=attempt + 1,
                        max_attempts=max_retries + 1,
                        delay=delay,
                        error=str(e)
                    )
                    
                    time.sleep(delay)
            
            # Should never reach here
            raise last_exception
        
        return wrapper
    return decorator
```

---

### Prompt Management

**Purpose**: External prompt storage and loading

**File**: `lib/llm/prompts/loader.py`

```python
from pathlib import Path
from typing import Dict, Any

PROMPTS_DIR = Path(__file__).parent

def load_prompt(category: str, name: str, variables: Dict[str, Any] = None) -> str:
    """
    Load prompt from file with variable substitution.
    
    Args:
        category: Prompt category (research, generation, analysis, validation, system)
        name: Prompt filename without .md extension
        variables: Dict of variables to substitute using {var} syntax
        
    Returns:
        Formatted prompt string
        
    Raises:
        FileNotFoundError: If prompt file doesn't exist
        KeyError: If required variable missing
        
    Example:
        >>> prompt = load_prompt('generation', 'product_names', {
        ...     'count': 100,
        ...     'industry': 'agtech',
        ...     'company_name': 'AgriTech Solutions',
        ...     'real_products': 'Tractor\\nHarvester\\nDrone',
        ...     'categories': 'Equipment\\nSoftware\\nServices'
        ... })
    """
    prompt_path = PROMPTS_DIR / category / f"{name}.md"
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt not found: {prompt_path}")
    
    prompt_template = prompt_path.read_text(encoding='utf-8')
    
    if variables:
        try:
            return prompt_template.format(**variables)
        except KeyError as e:
            raise KeyError(f"Missing required variable in prompt: {e}")
    
    return prompt_template

def load_system_prompt(role: str) -> str:
    """
    Load system prompt for specific role.
    
    Args:
        role: researcher, generator, or analyst
        
    Returns:
        System prompt string
        
    Example:
        >>> system = load_system_prompt('generator')
    """
    return load_prompt('system', role)
```

**Prompt Organization:**

```
lib/llm/prompts/
├── loader.py
├── research/                    # Script 02 prompts
│   ├── search_companies.md      # Exa search prompt
│   ├── analyze_website.md       # Analyze scraped content
│   ├── extract_products.md      # Extract product information
│   └── categorize_products.md   # Organize into categories
├── generation/                  # Scripts 03, 07, 08, 09 prompts
│   ├── product_names.md         # Generate product names (S03)
│   ├── product_page.md          # Generate product page content (S07)
│   ├── category_page.md         # Generate category page (S08)
│   ├── home_page.md             # Generate home page (S09)
│   ├── about_page.md            # Generate about page (S09)
│   ├── contact_page.md          # Generate contact page (S09)
│   ├── directory_entries.md     # Generate directory data (S06)
│   └── new_schema.md            # Generate schema YAML (S05)
├── analysis/                    # Script 04 prompts
│   ├── schema_relevance.md      # Evaluate schema relevance
│   └── propose_schemas.md       # Propose new schemas
├── validation/                  # Script 12 prompts
│   └── demo_features.md         # Generate demo features list
└── system/                      # System prompts for roles
    ├── researcher.md            # For research tasks (S02)
    ├── generator.md             # For content generation (S03,S06-S09)
    └── analyst.md               # For analysis tasks (S04,S12)
```

**Sample Prompt File:**

```markdown
<!-- lib/llm/prompts/generation/product_names.md -->
Generate {count} realistic product names for {company_name} in the {industry} industry.

Base them on these real products from market research:
{real_products}

Organize the products into these {category_count} categories:
{categories}

Requirements:
- Product names should sound professional and realistic
- Names should be similar to real products but not identical
- Distribute products evenly across all categories
- Include brief description for each product (1-2 sentences)

Return as JSON array with this format:
[
  {{
    "name": "Product Name",
    "category": "Category Name",
    "description": "Brief product description"
  }}
]
```

**Benefits:**

1. **Version Control**: Track prompt changes in git
2. **Easy Iteration**: Edit prompts without code changes
3. **Organized**: Clear structure by function
4. **Reusable**: Load same prompt in multiple contexts
5. **Testable**: Test prompts independently
6. **Pattern Match**: Similar to `backend/config/prompt_modules/`

---

### Retry Logic

### Custom Exceptions

**File**: `lib/errors/exceptions.py`

```python
class SiteGenError(Exception):
    """Base exception for site generator."""
    pass

class ConfigError(SiteGenError):
    """Configuration-related errors."""
    pass

class ConfigValidationError(ConfigError):
    """Config validation failed."""
    pass

class StateError(SiteGenError):
    """State management errors."""
    pass

class LLMError(SiteGenError):
    """LLM API errors."""
    pass

class LLMRetryExhausted(LLMError):
    """All LLM retry attempts failed."""
    pass

class ResearchError(SiteGenError):
    """Research/scraping errors."""
    pass

class ValidationError(SiteGenError):
    """Validation errors."""
    pass

class SchemaValidationError(ValidationError):
    """Schema validation failed."""
    pass

class LinkValidationError(ValidationError):
    """Link validation failed."""
    pass

class DataConsistencyError(ValidationError):
    """Data consistency check failed."""
    pass

class GenerationError(SiteGenError):
    """Content generation errors."""
    pass
```

### Error Handlers

**File**: `lib/errors/handlers.py`

```python
from typing import Callable, Any
from functools import wraps
from .exceptions import SiteGenError
from ..logging.logger import get_logger

logger = get_logger(__name__)

def handle_errors(
    reraise: bool = True,
    default_return: Any = None
) -> Callable:
    """
    Decorator for standardized error handling.
    
    Args:
        reraise: Whether to reraise exceptions after logging
        default_return: Value to return if error caught and not reraised
        
    Returns:
        Decorated function with error handling
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except SiteGenError as e:
                logger.error(
                    'site_gen_error',
                    function=func.__name__,
                    error_type=type(e).__name__,
                    error=str(e)
                )
                if reraise:
                    raise
                return default_return
            except Exception as e:
                logger.error(
                    'unexpected_error',
                    function=func.__name__,
                    error_type=type(e).__name__,
                    error=str(e)
                )
                if reraise:
                    raise SiteGenError(f"Unexpected error in {func.__name__}: {str(e)}") from e
                return default_return
        
        return wrapper
    return decorator
```

---

## Shared Utilities

### File Operations

**File**: `lib/io/file_ops.py`

```python
from pathlib import Path
from typing import Union, List

def ensure_dir(path: Union[str, Path]) -> Path:
    """
    Ensure directory exists, create if not.
    
    Args:
        path: Directory path
        
    Returns:
        Path object
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def read_text(path: Union[str, Path]) -> str:
    """
    Read text file.
    
    Args:
        path: File path
        
    Returns:
        File contents
    """
    return Path(path).read_text(encoding='utf-8')

def write_text(path: Union[str, Path], content: str) -> None:
    """
    Write text file.
    
    Args:
        path: File path
        content: Content to write
    """
    path = Path(path)
    ensure_dir(path.parent)
    path.write_text(content, encoding='utf-8')

def list_files(
    directory: Union[str, Path],
    pattern: str = "*",
    recursive: bool = False
) -> List[Path]:
    """
    List files in directory.
    
    Args:
        directory: Directory path
        pattern: Glob pattern
        recursive: Search recursively
        
    Returns:
        List of file paths
    """
    path = Path(directory)
    if recursive:
        return sorted(path.rglob(pattern))
    return sorted(path.glob(pattern))
```

### CSV Operations

**File**: `lib/io/csv_ops.py`

```python
import csv
from pathlib import Path
from typing import List, Dict, Any, Union

def read_csv(path: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Read CSV file into list of dictionaries.
    
    Args:
        path: CSV file path
        
    Returns:
        List of row dictionaries
    """
    with open(path, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def write_csv(
    path: Union[str, Path],
    rows: List[Dict[str, Any]],
    fieldnames: List[str]
) -> None:
    """
    Write list of dictionaries to CSV.
    
    Args:
        path: CSV file path
        rows: List of row dictionaries
        fieldnames: Column names
    """
    from .file_ops import ensure_dir
    
    path = Path(path)
    ensure_dir(path.parent)
    
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def validate_csv_structure(
    path: Union[str, Path],
    required_fields: List[str]
) -> bool:
    """
    Validate CSV has required fields.
    
    Args:
        path: CSV file path
        required_fields: Required column names
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If required fields missing
    """
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        
        missing = set(required_fields) - set(fieldnames)
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
    
    return True
```

### YAML Operations

**File**: `lib/io/yaml_ops.py`

```python
import yaml
from pathlib import Path
from typing import Any, Union, Dict

def read_yaml(path: Union[str, Path]) -> Dict[str, Any]:
    """
    Read YAML file.
    
    Args:
        path: YAML file path
        
    Returns:
        Parsed YAML content
    """
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}

def write_yaml(
    path: Union[str, Path],
    data: Dict[str, Any],
    default_flow_style: bool = False
) -> None:
    """
    Write YAML file.
    
    Args:
        path: YAML file path
        data: Data to write
        default_flow_style: YAML formatting style
    """
    from .file_ops import ensure_dir
    
    path = Path(path)
    ensure_dir(path.parent)
    
    with open(path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(data, f, default_flow_style=default_flow_style)
```

---

## Script Structure Template

Each script follows this pattern:

```python
#!/usr/bin/env python3
"""
Script XX: [Purpose]

Description of what this script does and its role in the workflow.
"""

import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / 'lib'))

from lib.config.config_loader import ConfigLoader
from lib.config.state_manager import StateManager
from lib.llm.client import LLMClient
from lib.errors.handlers import handle_errors
from lib.logging.logger import get_logger
# ... other imports specific to this script

logger = get_logger(__name__)

SCRIPT_NAME = "XX_script_name"

@handle_errors(reraise=True)
def main():
    """Main script execution."""
    logger.info('script_start', script=SCRIPT_NAME)
    
    # 1. Load configuration
    industry = sys.argv[1] if len(sys.argv) > 1 else 'agtech'
    industry_dir = Path(__file__).parent / industry
    
    config_path = industry_dir / 'site-gen-config.yaml'
    state_path = industry_dir / 'site-gen-state.yaml'
    
    # 2. Initialize config and state
    config = ConfigLoader(config_path).load()
    state = StateManager(state_path)
    state.load()
    
    # 3. Check if already completed
    if state.is_script_complete(SCRIPT_NAME):
        logger.info('script_already_complete', script=SCRIPT_NAME)
        print(f"✓ {SCRIPT_NAME} already completed. Use --force to rerun.")
        return
    
    # 4. Initialize LLM client
    llm = LLMClient(
        api_key=config.get('llm.api_key'),
        default_model=config.get('llm.models.generation')
    )
    
    # 5. Script-specific logic
    result = do_work(config, state, llm, industry_dir)
    
    # 6. Update state
    state.set(f'{SCRIPT_NAME}_result', result)
    state.mark_script_complete(SCRIPT_NAME)
    
    logger.info('script_complete', script=SCRIPT_NAME)
    print(f"✓ {SCRIPT_NAME} completed successfully")

def do_work(config, state, llm, industry_dir):
    """
    Script-specific work.
    
    Args:
        config: ConfigLoader instance
        state: StateManager instance
        llm: LLMClient instance
        industry_dir: Path to industry directory
        
    Returns:
        Result data
    """
    # Implementation specific to this script
    pass

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.warning('script_interrupted', script=SCRIPT_NAME)
        print(f"\n⚠ {SCRIPT_NAME} interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error('script_failed', script=SCRIPT_NAME, error=str(e))
        print(f"\n✗ {SCRIPT_NAME} failed: {str(e)}")
        sys.exit(1)
```

---

## Validation Module Examples

### Schema Validator

**File**: `lib/validation/schema_validator.py`

```python
from pathlib import Path
from typing import Dict, Any, List
from ..io.yaml_ops import read_yaml
from ..io.csv_ops import read_csv
from ..errors.exceptions import SchemaValidationError

def validate_csv_against_schema(
    csv_path: Path,
    schema_path: Path
) -> Dict[str, Any]:
    """
    Validate CSV data against schema definition.
    
    Args:
        csv_path: Path to CSV file
        schema_path: Path to schema YAML
        
    Returns:
        Validation report with errors and warnings
        
    Raises:
        SchemaValidationError: If validation fails critically
    """
    schema = read_yaml(schema_path)
    data = read_csv(csv_path)
    
    report = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'rows_checked': len(data)
    }
    
    required_fields = schema.get('required_fields', [])
    optional_fields = schema.get('optional_fields', [])
    all_fields = required_fields + optional_fields + ['name', 'tags']
    
    for idx, row in enumerate(data):
        # Check required fields present
        for field in required_fields:
            if not row.get(field):
                report['errors'].append({
                    'row': idx + 1,
                    'field': field,
                    'error': 'Required field missing or empty'
                })
                report['valid'] = False
        
        # Check no unexpected fields
        for field in row.keys():
            if field not in all_fields and not field.startswith('contact_info_'):
                report['warnings'].append({
                    'row': idx + 1,
                    'field': field,
                    'warning': 'Unexpected field not in schema'
                })
    
    if not report['valid']:
        raise SchemaValidationError(
            f"Schema validation failed with {len(report['errors'])} errors"
        )
    
    return report
```

### Link Validator

**File**: `lib/validation/link_validator.py`

```python
from pathlib import Path
from typing import Set, List, Dict
import re
from ..io.file_ops import list_files, read_text
from ..errors.exceptions import LinkValidationError

def validate_all_links(content_dir: Path) -> Dict[str, Any]:
    """
    Validate all internal markdown links.
    
    Args:
        content_dir: Path to content directory
        
    Returns:
        Validation report
        
    Raises:
        LinkValidationError: If broken links found
    """
    # Get all markdown files
    md_files = list_files(content_dir, pattern="*.md", recursive=True)
    
    # Build set of valid paths
    valid_paths = {
        f.relative_to(content_dir).as_posix()
        for f in md_files
    }
    
    report = {
        'valid': True,
        'broken_links': [],
        'files_checked': len(md_files)
    }
    
    # Check each file for links
    link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
    
    for md_file in md_files:
        content = read_text(md_file)
        matches = re.findall(link_pattern, content)
        
        for text, link in matches:
            # Skip external links
            if link.startswith('http'):
                continue
            
            # Resolve relative link
            link_path = (md_file.parent / link).relative_to(content_dir).as_posix()
            
            if link_path not in valid_paths:
                report['broken_links'].append({
                    'file': md_file.relative_to(content_dir).as_posix(),
                    'text': text,
                    'link': link,
                    'resolved': link_path
                })
                report['valid'] = False
    
    if not report['valid']:
        raise LinkValidationError(
            f"Found {len(report['broken_links'])} broken links"
        )
    
    return report
```

---

## Generation Module Examples

### Product Generator

**File**: `lib/generation/product_generator.py`

```python
from typing import List, Dict, Any
from ..llm.client import LLMClient
from ..logging.logger import get_logger

logger = get_logger(__name__)

def generate_product_names(
    real_products: List[str],
    categories: List[str],
    count: int,
    llm: LLMClient
) -> List[Dict[str, str]]:
    """
    Generate realistic product names based on research.
    
    Args:
        real_products: List of real product names from research
        categories: List of product categories
        count: Number of products to generate
        llm: LLM client
        
    Returns:
        List of product dicts with name, category, description
    """
    prompt = f"""Based on these real products:
{chr(10).join(f'- {p}' for p in real_products[:20])}

Generate {count} realistic product names distributed across these categories:
{chr(10).join(f'- {c}' for c in categories)}

Return JSON array with format:
[{{"name": "Product Name", "category": "Category", "description": "Brief description"}}]

Make names sound professional and realistic, similar to real products but not identical.
"""
    
    response = llm.generate_text(
        prompt=prompt,
        system_prompt="You are an expert at naming products in this industry.",
        temperature=0.8
    )
    
    # Parse JSON response
    import json
    products = json.loads(response)
    
    logger.info('products_generated', count=len(products))
    
    return products
```

### Directory Generator

**File**: `lib/generation/directory_generator.py`

```python
from pathlib import Path
from typing import List, Dict, Any
from ..llm.client import LLMClient
from ..io.yaml_ops import read_yaml
from ..io.csv_ops import write_csv
from ..logging.logger import get_logger

logger = get_logger(__name__)

def generate_directory_csv(
    schema_path: Path,
    product_list: List[Dict[str, Any]],
    llm: LLMClient,
    output_path: Path,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate coherent CSV data for any schema.
    
    Args:
        schema_path: Path to schema YAML
        product_list: List of products for references
        llm: LLM client
        output_path: Where to write CSV
        config: Site generation config
        
    Returns:
        Generation report
    """
    schema = read_yaml(schema_path)
    schema_name = schema['entry_type']
    
    logger.info('directory_generation_start', schema=schema_name)
    
    # Build prompt with schema structure
    prompt = f"""Generate CSV data for schema: {schema_name}

Schema fields:
Required: {schema.get('required_fields', [])}
Optional: {schema.get('optional_fields', [])}

Available products for references:
{format_product_list(product_list[:20])}

Generate 20-30 realistic entries following this schema.
Ensure all relationships reference valid product IDs.

Return JSON array format.
"""
    
    response = llm.generate_text(
        prompt=prompt,
        system_prompt=f"You are generating directory data for {config['company']['name']}.",
        temperature=0.7
    )
    
    # Parse and write CSV
    import json
    entries = json.loads(response)
    
    fieldnames = ['name', 'tags'] + schema.get('required_fields', []) + schema.get('optional_fields', [])
    
    write_csv(output_path, entries, fieldnames)
    
    logger.info('directory_generation_complete', schema=schema_name, count=len(entries))
    
    return {
        'schema': schema_name,
        'entries_generated': len(entries),
        'output_path': str(output_path)
    }

def format_product_list(products: List[Dict[str, Any]]) -> str:
    """Format product list for prompt."""
    return '\n'.join(
        f"- {p['name']} (ID: {p['id']}, Category: {p['category']})"
        for p in products
    )
```

---

## Logging

**File**: `lib/logging/logger.py`

```python
import sys
from pathlib import Path

# Add backend to path to leverage existing logger
backend_path = Path(__file__).parent.parent.parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

try:
    import logfire
    
    def get_logger(name: str):
        """Get logger instance using backend's logfire."""
        return logfire
        
except ImportError:
    # Fallback to standard logging if logfire not available
    import logging
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    def get_logger(name: str):
        """Get standard logger as fallback."""
        return logging.getLogger(name)
```

---

## Usage Examples

### Example: Script 01 (Init Config)

```python
from lib.config.config_loader import ConfigLoader
from lib.config.state_manager import StateManager
from lib.io.yaml_ops import write_yaml

def create_initial_config(industry_dir: Path) -> Dict[str, Any]:
    """Create initial config based on user input."""
    
    # Interactive prompts
    company_name = input("Company name: ")
    tagline = input("Tagline: ")
    
    # Read research files
    research_files = list(industry_dir.glob("research/*.md"))
    
    config = {
        'company': {
            'name': company_name,
            'industry': industry_dir.name,
            'tagline': tagline
        },
        'research': {
            'reference_files': [f.name for f in research_files]
        },
        'llm': {
            'api_key': '${OPENROUTER_API_KEY}',
            'models': {
                'tool_calling': 'anthropic/claude-sonnet-4.5',
                'generation': 'anthropic/claude-haiku-4.5'
            }
        },
        'generation': {
            'products': {'count': 100, 'categories': 10},
            'relationships': {'max_per_product': 3}
        }
    }
    
    # Write config
    config_path = industry_dir / 'site-gen-config.yaml'
    write_yaml(config_path, config)
    
    # Initialize state
    state = StateManager(industry_dir / 'site-gen-state.yaml')
    state.load()
    state.mark_script_complete('01_init_config')
    
    return config
```

### Example: Script 03 (Generate Product Schema)

```python
from lib.config.config_loader import ConfigLoader
from lib.llm.client import LLMClient
from lib.generation.product_generator import generate_product_names
from lib.io.csv_ops import write_csv

def generate_products(config, state, llm, industry_dir):
    """Generate product directory CSV."""
    
    # Load research data
    research_file = industry_dir / 'research' / 'products-catalog.json'
    with open(research_file) as f:
        real_products = json.load(f)
    
    # Get product names from research
    product_names = [p['name'] for p in real_products]
    
    # Generate config
    gen_config = config.get('generation')
    product_count = gen_config['products']['count']
    category_count = gen_config['products']['categories']
    
    # Generate categories first
    categories = generate_categories(product_names, category_count, llm)
    
    # Generate products
    products = generate_product_names(
        real_products=product_names,
        categories=categories,
        count=product_count,
        llm=llm
    )
    
    # Add IDs and write CSV
    for idx, product in enumerate(products, 1):
        product['id'] = f"prod_{idx:04d}"
    
    output_path = industry_dir / 'data' / 'product.csv'
    write_csv(
        path=output_path,
        rows=products,
        fieldnames=['id', 'name', 'category', 'description', 'tags']
    )
    
    return {
        'products_generated': len(products),
        'categories': categories,
        'output': str(output_path)
    }
```

---

## Summary

**Key Patterns:**

1. **ConfigLoader**: Immutable config loaded once
2. **StateManager**: Mutable progress tracking
3. **LLMClient**: Unified LLM access with retry
4. **Function Organization**: lib/ organized by domain
5. **Error Handling**: Standardized exceptions and handlers
6. **Logging**: Leverage backend logfire
7. **Script Template**: Consistent structure across all scripts

**Reuse Strategy:**

- Common utilities in `lib/io/`
- Validation functions in `lib/validation/`
- Generation functions in `lib/generation/`
- Shared config/state management
- Centralized error handling and logging

**Benefits:**

- High code reuse across scripts
- Easy to test individual functions
- Clear separation of concerns
- Maintainable and debuggable
- Extensible for future industries
