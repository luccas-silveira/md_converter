"""
Utilities for loading environment variables from `.env` files.
"""

from __future__ import annotations

import os
from pathlib import Path

# Project root (one level above /config)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _strip_inline_comment(value: str) -> str:
    """Remove inline comments while respecting quoted values."""
    result = []
    quote_char = None

    for char in value:
        if char in {"'", '"'}:
            if quote_char == char:
                quote_char = None
            elif quote_char is None:
                quote_char = char

        if char == "#" and quote_char is None:
            break

        result.append(char)

    return "".join(result).strip()


def _clean_value(raw_value: str) -> str:
    """Normalize .env value by trimming whitespace and wrapping quotes."""
    value = raw_value.strip()
    value = _strip_inline_comment(value)

    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]

    return value


def load_env_from_file(filename: str = ".env") -> None:
    """
    Load environment variables from a local .env file if present.

    - Supports lines prefixed with `export`.
    - Ignores comments and blank lines.
    - Only overrides unset or empty environment variables.
    """
    env_path = PROJECT_ROOT / filename
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        if line.startswith("export "):
            line = line[7:].strip()
            if not line:
                continue

        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue

        cleaned_value = _clean_value(value)

        current_value = os.environ.get(key)
        if current_value is None or current_value.strip() == "":
            os.environ[key] = cleaned_value
