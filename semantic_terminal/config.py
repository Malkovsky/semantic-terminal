"""Configuration loading and persistence from environment variables and config file."""

from __future__ import annotations

import json
import os
import platform
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path

DEFAULT_MODEL = "llama-3.3-70b-versatile"
DEFAULT_API_BASE = "https://api.groq.com/openai/v1"
CONFIG_DIR = Path.home() / ".config" / "semantic-terminal"
CONFIG_FILE = CONFIG_DIR / "config.json"

VALID_KEYS = {"api_key", "api_base", "model"}


@dataclass
class Config:
    api_key: str = ""
    api_base: str = DEFAULT_API_BASE
    model: str = DEFAULT_MODEL

    def validate(self) -> None:
        """Raise if required fields are missing."""
        if not self.api_key:
            raise SystemExit(
                "Error: No API key configured.\n"
                "Run `sem config` to set up your configuration,\n"
                "or set the SEM_API_KEY (or GROQ_API_KEY) environment variable.\n"
                "\n"
                "Get a free API key at: https://console.groq.com"
            )


def mask_api_key(key: str) -> str:
    """Return a masked version of *key*, showing only the last 4 characters.

    Examples:
        >>> mask_api_key("sk-abc123xY")
        'sk-...23xY'
        >>> mask_api_key("")
        '(not set)'
    """
    if not key:
        return "(not set)"
    if len(key) <= 8:
        return "****"
    # Preserve the prefix up to the first dash (e.g. "sk-") if present
    dash = key.find("-")
    prefix = key[: dash + 1] if 0 < dash < 6 else ""
    return f"{prefix}...{key[-4:]}"


def _load_config_file() -> dict:
    """Load config from the JSON config file, returning an empty dict on failure."""
    if not CONFIG_FILE.is_file():
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _set_file_permissions(path: Path) -> None:
    """Restrict file to owner read/write only (0600 on Unix, ACL on Windows)."""
    if platform.system() == "Windows":
        try:
            username = os.environ.get("USERNAME", "")
            if username:
                # Remove inherited permissions and grant only current user
                subprocess.run(
                    ["icacls", str(path), "/inheritance:r",
                     "/grant:r", f"{username}:(R,W)"],
                    capture_output=True,
                    check=False,
                )
        except OSError:
            pass  # Best effort on Windows
    else:
        try:
            path.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 0600
        except OSError:
            pass


def save_config_file(data: dict) -> None:
    """Write *data* as JSON to the config file with restrictive permissions.

    Creates ``CONFIG_DIR`` if it doesn't exist.  Only writes keys that are in
    ``VALID_KEYS``.
    """
    # Filter to valid keys only
    filtered = {k: v for k, v in data.items() if k in VALID_KEYS}

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(filtered, f, indent=2)
        f.write("\n")

    _set_file_permissions(CONFIG_FILE)


def load_config(*, model_override: str | None = None) -> Config:
    """Build a Config by layering env vars over the config file.

    Priority (highest to lowest):
      1. CLI flag overrides (model_override)
      2. Environment variables (SEM_API_KEY, SEM_API_BASE, SEM_MODEL)
      3. Fallback env vars (GROQ_API_KEY, OPENAI_API_KEY)
      4. Config file (~/.config/semantic-terminal/config.json)
      5. Built-in defaults
    """
    file_cfg = _load_config_file()

    api_key = (
        os.environ.get("SEM_API_KEY")
        or os.environ.get("GROQ_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or file_cfg.get("api_key", "")
    )

    api_base = (
        os.environ.get("SEM_API_BASE")
        or file_cfg.get("api_base", "")
        or DEFAULT_API_BASE
    )

    model = (
        model_override
        or os.environ.get("SEM_MODEL")
        or file_cfg.get("model", "")
        or DEFAULT_MODEL
    )

    return Config(api_key=api_key, api_base=api_base, model=model)


def get_config_sources() -> dict[str, str]:
    """Return a mapping of config key -> source label for display purposes.

    Sources: "env var", "config file", "default".
    """
    file_cfg = _load_config_file()
    sources: dict[str, str] = {}

    # api_key
    if os.environ.get("SEM_API_KEY"):
        sources["api_key"] = "SEM_API_KEY env var"
    elif os.environ.get("GROQ_API_KEY"):
        sources["api_key"] = "GROQ_API_KEY env var"
    elif os.environ.get("OPENAI_API_KEY"):
        sources["api_key"] = "OPENAI_API_KEY env var"
    elif file_cfg.get("api_key"):
        sources["api_key"] = "config file"
    else:
        sources["api_key"] = "default"

    # api_base
    if os.environ.get("SEM_API_BASE"):
        sources["api_base"] = "SEM_API_BASE env var"
    elif file_cfg.get("api_base"):
        sources["api_base"] = "config file"
    else:
        sources["api_base"] = "default"

    # model
    if os.environ.get("SEM_MODEL"):
        sources["model"] = "SEM_MODEL env var"
    elif file_cfg.get("model"):
        sources["model"] = "config file"
    else:
        sources["model"] = "default"

    return sources
