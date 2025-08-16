from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import os

import yaml
from dotenv import load_dotenv, find_dotenv


# Load environment variables once (system env takes precedence over .env)
load_dotenv(find_dotenv(), override=False)

_CONFIG_CACHE: Dict[str, Any] | None = None


def load_config() -> Dict[str, Any]:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE

    config_path = Path(__file__).resolve().parent.parent / "config" / "app.yaml"
    config: Dict[str, Any] = {}
    if config_path.exists():
        try:
            config = yaml.safe_load(config_path.read_text()) or {}
        except Exception:
            config = {}

    # Defaults and validation
    chat = config.setdefault("chat", {})
    input_cfg = chat.setdefault("input", {})
    input_cfg.setdefault("debounce_ms", 250)
    input_cfg.setdefault("submit_shortcut", "ctrl+enter")
    input_cfg.setdefault("enter_inserts_newline", True)

    # UI defaults
    ui_cfg = config.setdefault("ui", {})
    ui_cfg.setdefault("sse_enabled", True)
    ui_cfg.setdefault("allow_basic_html", True)

    # Logging defaults
    logging_cfg = config.setdefault("logging", {})
    logging_cfg.setdefault("level", "INFO")
    logging_cfg.setdefault("path", "./backend/logs/app.jsonl")
    logging_cfg.setdefault("rotation", "50 MB")
    logging_cfg.setdefault("retention", "14 days")
    logging_cfg.setdefault("frontend_debug", False)

    # LLM defaults with basic validation
    llm_cfg = config.setdefault("llm", {})
    llm_cfg.setdefault("provider", "openrouter")
    llm_cfg.setdefault("model", "openai/gpt-oss-20b:free")
    try:
        temp = float(llm_cfg.get("temperature", 0.3))
        if not (0.0 <= temp <= 2.0):
            temp = 0.3
        llm_cfg["temperature"] = temp
    except Exception:
        llm_cfg["temperature"] = 0.3
    try:
        max_toks = int(llm_cfg.get("max_tokens", 512))
        if max_toks <= 0:
            max_toks = 512
        llm_cfg["max_tokens"] = max_toks
    except Exception:
        llm_cfg["max_tokens"] = 512

    _CONFIG_CACHE = config
    return config
def get_env(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)


def get_openrouter_api_key() -> str | None:
    return get_env("OPENROUTER_API_KEY")




