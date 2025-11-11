"""
Prompt module system for configurable prompt enhancements.

Modules are markdown files stored in:
- System-level: backend/config/prompt_modules/system/
- Account-level: backend/config/prompt_modules/accounts/{account_slug}/

Modules are selected based on agent config and injected into system prompt.
"""

from pathlib import Path
from typing import Optional
import logfire


def _find_backend_root() -> Path:
    """
    Find backend/ directory (contains app/ and config/ subdirectories).
    
    Walks up from current file until it finds a directory named 'backend'
    that contains both 'app/' and 'config/' subdirectories.
    
    Returns:
        Path to backend/ directory
        
    Raises:
        RuntimeError: If backend/ directory cannot be found
    """
    current = Path(__file__).resolve()
    
    for parent in [current] + list(current.parents):
        if parent.name == "backend" and (parent / "app").is_dir() and (parent / "config").is_dir():
            logfire.debug("backend.root.found", path=str(parent))
            return parent
    
    raise RuntimeError(
        f"Could not find backend/ directory from {current}. "
        "Expected to find backend/app/ and backend/config/ structure."
    )


# Calculate backend root once at module import
BACKEND_ROOT = _find_backend_root()
SYSTEM_MODULES_DIR = BACKEND_ROOT / "config" / "prompt_modules" / "system"
ACCOUNT_MODULES_DIR = BACKEND_ROOT / "config" / "prompt_modules" / "accounts"


def load_prompt_module(module_name: str, account_slug: Optional[str] = None) -> Optional[str]:
    """
    Load a prompt module from markdown file.
    
    Args:
        module_name: Name of module (e.g., "tool_calling_few_shot")
        account_slug: Optional account slug for account-specific modules
        
    Returns:
        Module content as string, or None if not found
        
    Example:
        content = load_prompt_module("tool_calling_few_shot")
        # Loads: backend/config/prompt_modules/system/tool_calling_few_shot.md
    """
    # Try account-level first (if specified)
    if account_slug:
        account_path = ACCOUNT_MODULES_DIR / account_slug / f"{module_name}.md"
        if account_path.exists():
            logfire.info('prompt.module.load.account', 
                        module_name=module_name, 
                        account=account_slug,
                        path=str(account_path))
            return account_path.read_text()
    
    # Fall back to system-level
    system_path = SYSTEM_MODULES_DIR / f"{module_name}.md"
    if system_path.exists():
        logfire.info('prompt.module.load.system', 
                    module_name=module_name,
                    path=str(system_path))
        return system_path.read_text()
    
    logfire.warn('prompt.module.not_found', 
                module_name=module_name, 
                account=account_slug)
    return None


def load_modules_for_agent(agent_config: dict, account_slug: Optional[str] = None) -> str:
    """
    Load all enabled prompt modules for an agent based on config.
    
    Args:
        agent_config: Agent configuration from config.yaml
        account_slug: Optional account slug for account-specific modules
        
    Returns:
        Combined module content as string
        
    Example config.yaml:
        prompting:
          modules:
            enabled: true
            selected:
              - tool_calling_few_shot
              - tool_calling_cot
              - tool_calling_structured
    """
    modules_config = agent_config.get("prompting", {}).get("modules", {})
    
    if not modules_config.get("enabled", False):
        logfire.info('prompt.module.disabled')
        return ""
    
    selected_modules = modules_config.get("selected", [])
    
    if not selected_modules:
        logfire.info('prompt.module.none_selected')
        return ""
    
    logfire.info('prompt.module.loading', 
                module_count=len(selected_modules),
                modules=selected_modules)
    
    # Load each module
    module_contents = []
    for module_name in selected_modules:
        content = load_prompt_module(module_name, account_slug)
        if content:
            module_contents.append(content)
    
    if not module_contents:
        logfire.warn('prompt.module.none_loaded', 
                    requested=selected_modules)
        return ""
    
    # Combine with separators
    combined = "\n\n---\n\n".join(module_contents)
    logfire.info('prompt.module.loaded', 
                loaded_count=len(module_contents),
                total_chars=len(combined))
    
    return combined

