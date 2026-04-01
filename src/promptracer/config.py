"""Project-level configuration via .promptracer.yaml."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_CONFIG_NAMES = [".promptracer.yaml", ".promptracer.yml", "promptracer.yaml"]


def find_config(start: Path | None = None) -> Path | None:
    """Walk up from start directory to find a config file."""
    current = start or Path.cwd()
    for _ in range(20):  # max depth
        for name in _CONFIG_NAMES:
            config_path = current / name
            if config_path.exists():
                return config_path
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Load config from file or auto-discover.

    Example .promptracer.yaml:
        default_model: openai/gpt-4o
        default_judge: openai/gpt-4o-mini
        models:
          - openai/gpt-4o
          - anthropic/claude-sonnet-4-6
          - ollama/llama3
        criteria: "accuracy, relevance, and completeness"
        track_costs: true
    """
    if path is None:
        path = find_config()
    if path is None or not path.exists():
        return {}
    return yaml.safe_load(path.read_text()) or {}


def get(key: str, default: Any = None) -> Any:
    """Get a config value."""
    config = load_config()
    return config.get(key, default)
