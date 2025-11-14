"""
Prompt breakdown service for capturing LLM prompt composition metadata.

This service provides centralized tracking of how LLM prompts are assembled,
enabling debugging of tool selection and prompt composition issues in the admin UI.
"""
from typing import Dict, Optional
import logfire


class PromptBreakdownService:
    """
    Centralized service for capturing prompt breakdown metadata.
    Used by all agents to track prompt composition for admin debugging.
    """
    
    @staticmethod
    def capture_breakdown(
        base_prompt: str,
        critical_rules: Optional[str] = None,
        directory_docs: Optional[str] = None,
        modules: Optional[Dict[str, str]] = None,
        account_slug: Optional[str] = None,
        agent_instance_slug: Optional[str] = None
    ) -> dict:
        """
        Capture prompt breakdown with character counts and sources.
        
        Args:
            base_prompt: Base system prompt content
            critical_rules: Critical tool selection rules (injected at top)
            directory_docs: Auto-generated directory documentation
            modules: Dict of {module_name: content} for additional modules
            account_slug: Account identifier for logging
            agent_instance_slug: Agent instance identifier for logging
            
        Returns:
            Dict suitable for storing in llm_requests.meta['prompt_breakdown']
            Format: {
                "sections": [
                    {"name": "critical_rules", "position": 1, "char_count": 4928, "source": "tool_selection_hints.md"},
                    {"name": "base_prompt", "position": 2, "char_count": 3200, "source": "system_prompt.md"},
                    ...
                ],
                "total_char_count": 15410
            }
        """
        breakdown = {
            "sections": []
        }
        
        position = 1
        total_chars = 0
        
        # 1. Critical rules (if present, injected at top)
        if critical_rules:
            breakdown["sections"].append({
                "name": "critical_rules",
                "position": position,
                "char_count": len(critical_rules),
                "source": "tool_selection_hints.md"
            })
            total_chars += len(critical_rules)
            position += 1
        
        # 2. Base system prompt
        breakdown["sections"].append({
            "name": "base_prompt",
            "position": position,
            "char_count": len(base_prompt),
            "source": "system_prompt.md"
        })
        total_chars += len(base_prompt)
        position += 1
        
        # 3. Directory documentation (if present)
        if directory_docs:
            breakdown["sections"].append({
                "name": "directory_docs",
                "position": position,
                "char_count": len(directory_docs),
                "source": "auto-generated"
            })
            total_chars += len(directory_docs)
            position += 1
        
        # 4. Additional modules
        if modules:
            for module_name, content in modules.items():
                breakdown["sections"].append({
                    "name": module_name,
                    "position": position,
                    "char_count": len(content),
                    "source": f"{module_name}.md"
                })
                total_chars += len(content)
                position += 1
        
        # Add summary
        breakdown["total_char_count"] = total_chars
        
        # Log breakdown for monitoring
        logfire.info(
            'service.prompt_breakdown.captured',
            account_slug=account_slug,
            agent_instance_slug=agent_instance_slug,
            total_chars=total_chars,
            section_count=len(breakdown["sections"])
        )
        
        return breakdown

