"""
Configuration specifications for agent parameters.

This module defines the parameter specifications for model settings and tool configurations,
separating configuration data from cascade logic for better maintainability.
"""

# Copyright (c) 2025 Ape4, Inc. All rights reserved.
# Unauthorized copying of this file is strictly prohibited.

from typing import Dict, Any


# Model parameter specifications with cascade configuration
MODEL_PARAMETER_SPECS: Dict[str, Dict[str, Any]] = {
    "model": {
        "agent_path": "model_settings.model",
        "global_path": "llm.model", 
        "fallback": "deepseek/deepseek-chat-v3.1"
    },
    "temperature": {
        "agent_path": "model_settings.temperature",
        "global_path": "llm.temperature",
        "fallback": 0.7
    },
    "max_tokens": {
        "agent_path": "model_settings.max_tokens", 
        "global_path": "llm.max_tokens",
        "fallback": 1024
    }
}


# Tool parameter specifications with cascade configuration
TOOL_PARAMETER_SPECS: Dict[str, Dict[str, Dict[str, Any]]] = {
    "vector_search": {
        "enabled": {
            "agent_path": "tools.vector_search.enabled",
            "fallback": True
        },
        "max_results": {
            "agent_path": "tools.vector_search.max_results",
            "fallback": 5
        },
        "similarity_threshold": {
            "agent_path": "tools.vector_search.similarity_threshold",
            "fallback": 0.7
        },
        "namespace_isolation": {
            "agent_path": "tools.vector_search.namespace_isolation",
            "fallback": True
        }
    },
    "web_search": {
        "enabled": {
            "agent_path": "tools.web_search.enabled",
            "fallback": False
        },
        "provider": {
            "agent_path": "tools.web_search.provider",
            "fallback": "exa"
        },
        "max_results": {
            "agent_path": "tools.web_search.max_results",
            "fallback": 10
        }
    },
    "conversation_management": {
        "enabled": {
            "agent_path": "tools.conversation_management.enabled",
            "fallback": True
        },
        "auto_summarize_threshold": {
            "agent_path": "tools.conversation_management.auto_summarize_threshold",
            "fallback": 10
        }
    },
    "profile_capture": {
        "enabled": {
            "agent_path": "tools.profile_capture.enabled",
            "fallback": False
        }
    },
    "email_summary": {
        "enabled": {
            "agent_path": "tools.email_summary.enabled",
            "fallback": False
        }
    }
}

