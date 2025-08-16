from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml


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

    # Defaults
    chat = config.setdefault("chat", {})
    input_cfg = chat.setdefault("input", {})
    input_cfg.setdefault("debounce_ms", 250)
    input_cfg.setdefault("submit_shortcut", "ctrl+enter")
    input_cfg.setdefault("enter_inserts_newline", True)

    _CONFIG_CACHE = config
    return config


