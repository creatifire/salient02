"""
Prompt breakdown service for capturing LLM prompt composition metadata.

This service provides centralized tracking of how LLM prompts are assembled,
enabling debugging of tool selection and prompt composition issues in the admin UI.
"""
from typing import Dict, Optional, TYPE_CHECKING
import logfire

if TYPE_CHECKING:
    from ..agents.tools.prompt_generator import DirectoryDocsResult


class PromptBreakdownService:
    """
    Centralized service for capturing prompt breakdown metadata.
    Used by all agents to track prompt composition for admin debugging.
    """
    
    @staticmethod
    def capture_breakdown(
        base_prompt: str,
        critical_rules: Optional[str] = None,
        directory_result: Optional['DirectoryDocsResult'] = None,
        modules: Optional[Dict[str, str]] = None,
        account_slug: Optional[str] = None,
        agent_instance_slug: Optional[str] = None
    ) -> dict:
        """
        Capture prompt breakdown with full content for each module.
        
        Args:
            base_prompt: Base system prompt content
            critical_rules: Critical tool selection rules (injected at top)
            directory_result: Structured directory docs (header + sections) from DirectoryDocsResult
            modules: Dict of {module_name: content} for additional modules
            account_slug: Account identifier for logging
            agent_instance_slug: Agent instance identifier for logging
            
        Returns:
            Dict suitable for storing in llm_requests.meta['prompt_breakdown']
            Format: {
                "sections": [
                    {
                        "name": "tool_selection_hints.md", 
                        "position": 1, 
                        "characters": 4928, 
                        "source": "tool_selection_hints.md",
                        "content": "...",
                        "type": "module"
                    },
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
        # Note: critical_rules includes the separator "\n\n---\n\n" (7 chars) added in simple_chat.py
        if critical_rules:
            breakdown["sections"].append({
                "name": "tool_selection_hints.md",
                "position": position,
                "characters": len(critical_rules),  # Already includes separator
                "source": "tool_selection_hints.md",
                "content": critical_rules,
                "type": "module"
            })
            total_chars += len(critical_rules)
            position += 1
        
        # 2. Base system prompt
        breakdown["sections"].append({
            "name": "system_prompt.md",
            "position": position,
            "characters": len(base_prompt),
            "source": "system_prompt.md",
            "content": base_prompt,
            "type": "module"
        })
        total_chars += len(base_prompt)
        position += 1
        
        # 3. Directory documentation (structured)
        # Note: A "\n\n" separator (2 chars) is added before directory_docs in simple_chat.py
        if directory_result:
            # Add separator characters that precede directory content
            total_chars += 2  # "\n\n" separator before directory_docs
            
            header_position = None
            
            # 3a. Directory header (if multi-directory)
            if directory_result.header_section:
                header_position = position
                header_section = directory_result.header_section
                breakdown["sections"].append({
                    "name": header_section.name,
                    "position": position,
                    "characters": header_section.character_count,
                    "source": header_section.metadata.get("source", "auto-generated"),
                    "content": header_section.content,
                    "type": "directory_header",
                    "metadata": header_section.metadata
                })
                total_chars += header_section.character_count
                position += 1
            
            # 3b. Individual directory sections
            for dir_section in directory_result.directory_sections:
                section_dict = {
                    "name": dir_section.name,
                    "position": position,
                    "characters": dir_section.character_count,
                    "source": f"auto-generated ({dir_section.metadata.get('schema_file', 'N/A')})",
                    "content": dir_section.content,
                    "type": "directory",
                    "metadata": dir_section.metadata
                }
                if header_position is not None:
                    section_dict["parent_position"] = header_position
                
                breakdown["sections"].append(section_dict)
                total_chars += dir_section.character_count
                position += 1
        
        # 4. Additional modules
        # Note: A "\n\n" separator (2 chars) is added before modules,
        # and "\n\n---\n\n" (7 chars) between each module in simple_chat.py
        if modules:
            # Add separator before first module
            total_chars += 2  # "\n\n" separator before combined modules
            
            module_count = 0
            for module_name, content in modules.items():
                # Add inter-module separator (except before first module)
                if module_count > 0:
                    total_chars += 7  # "\n\n---\n\n" between modules
                
                breakdown["sections"].append({
                    "name": f"{module_name}.md",
                    "position": position,
                    "characters": len(content),
                    "source": f"{module_name}.md",
                    "content": content,
                    "type": "module"
                })
                total_chars += len(content)
                position += 1
                module_count += 1
        
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

