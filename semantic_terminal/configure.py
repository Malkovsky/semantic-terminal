"""Interactive configuration wizard and config management commands."""

from __future__ import annotations

import getpass
import re
import sys

from .config import (
    CONFIG_FILE,
    DEFAULT_API_BASE,
    DEFAULT_MODEL,
    VALID_KEYS,
    _load_config_file,
    get_config_sources,
    load_config,
    mask_api_key,
    save_config_file,
)


def _prompt_hidden(prompt: str) -> str:
    """Prompt for sensitive input with no echo."""
    try:
        return getpass.getpass(prompt)
    except (EOFError, KeyboardInterrupt):
        print()
        raise SystemExit(0)


def _prompt(prompt: str) -> str:
    """Prompt for regular input."""
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print()
        raise SystemExit(0)


def _validate_url(url: str) -> bool:
    """Check that *url* looks like a valid HTTP(S) base URL."""
    return bool(re.match(r"^https?://\S+", url))


# ── Interactive wizard ───────────────────────────────────────────────────────


def run_wizard() -> None:
    """Guide the user through setting all config values interactively."""
    file_cfg = _load_config_file()

    current_key = file_cfg.get("api_key", "")
    current_base = file_cfg.get("api_base", "") or DEFAULT_API_BASE
    current_model = file_cfg.get("model", "") or DEFAULT_MODEL

    print()
    print("Semantic Terminal Configuration")
    print("\u2500" * 31)
    print()

    # --- API Base URL (provider) ---
    new_base = _prompt(f"  API Base URL [{current_base}]: ")
    api_base = new_base.strip() if new_base.strip() else current_base

    if api_base and not _validate_url(api_base):
        raise SystemExit(f"Error: Invalid URL: {api_base}")

    # --- API Key (hidden input) ---
    masked = mask_api_key(current_key)
    new_key = _prompt_hidden(f"  API Key [{masked}]: ")
    api_key = new_key.strip() if new_key.strip() else current_key

    # --- Model ---
    new_model = _prompt(f"  Model [{current_model}]: ")
    model = new_model.strip() if new_model.strip() else current_model

    # --- Save ---
    data = {"api_key": api_key, "api_base": api_base, "model": model}
    save_config_file(data)

    print()
    print(f"  Configuration saved to {CONFIG_FILE}")
    print()


# ── Show current config ─────────────────────────────────────────────────────


def run_show() -> None:
    """Display the effective configuration with the API key masked."""
    config = load_config()
    sources = get_config_sources()

    def _source_note(key: str) -> str:
        src = sources.get(key, "")
        if "env var" in src:
            return f"  (from {src})"
        return ""

    print()
    print(f"  API Base URL: {config.api_base}{_source_note('api_base')}")
    print(f"  API Key:      {mask_api_key(config.api_key)}{_source_note('api_key')}")
    print(f"  Model:        {config.model}{_source_note('model')}")
    print()
    print(f"  Config file:  {CONFIG_FILE}")
    print()


# ── Set a single config value ────────────────────────────────────────────────


def run_set(key: str, value: str | None = None) -> None:
    """Set a single config key in the config file.

    For ``api_key``, *value* should be ``None`` — the user will be prompted
    interactively so the secret never appears in shell history.
    """
    if key not in VALID_KEYS:
        valid = ", ".join(sorted(VALID_KEYS))
        raise SystemExit(f"Error: Unknown config key '{key}'. Valid keys: {valid}")

    file_cfg = _load_config_file()

    if key == "api_key":
        if value is not None:
            print(
                "Warning: Passing the API key as an argument exposes it in "
                "shell history."
            )
            print("For security, you will be prompted to enter it instead.")
            print()
        new_value = _prompt_hidden("  API Key: ")
        if not new_value.strip():
            raise SystemExit("Error: API key cannot be empty.")
        file_cfg["api_key"] = new_value.strip()
    else:
        if value is None:
            raise SystemExit(
                f"Error: Value required. Usage: sem config set {key} <value>"
            )
        if key == "api_base" and not _validate_url(value):
            raise SystemExit(f"Error: Invalid URL: {value}")
        file_cfg[key] = value

    save_config_file(file_cfg)
    display = mask_api_key(file_cfg[key]) if key == "api_key" else file_cfg[key]
    print(f"  {key} set to {display}")
