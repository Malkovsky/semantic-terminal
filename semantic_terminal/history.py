"""Persist and recall command history for CLI shortcuts."""

from __future__ import annotations

import json
from pathlib import Path

DATA_DIR = Path.home() / ".local" / "share" / "semantic-terminal"
LAST_COMMAND_FILE = DATA_DIR / "last_command"
LAST_INTERACTION_FILE = DATA_DIR / "last_interaction.json"


def save_last_command(command: str) -> None:
    """Write *command* to the history file, creating directories as needed."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LAST_COMMAND_FILE.write_text(command, encoding="utf-8")


def load_last_command() -> str | None:
    """Return the last saved command, or ``None`` if none exists."""
    if not LAST_COMMAND_FILE.is_file():
        return None
    text = LAST_COMMAND_FILE.read_text(encoding="utf-8").strip()
    return text or None


def save_last_interaction(request: str, command: str) -> None:
    """Write the last request-command pair to JSON history."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "request": request,
        "command": command,
    }
    LAST_INTERACTION_FILE.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )


def load_last_interaction() -> tuple[str | None, str | None]:
    """Return ``(request, command)`` for last interaction, else ``(None, None)``."""
    if not LAST_INTERACTION_FILE.is_file():
        return (None, None)

    try:
        data = json.loads(LAST_INTERACTION_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return (None, None)

    if not isinstance(data, dict):
        return (None, None)

    request = data.get("request")
    command = data.get("command")

    if not isinstance(request, str) or not isinstance(command, str):
        return (None, None)

    request = request.strip()
    command = command.strip()
    if not request or not command:
        return (None, None)

    return (request, command)
