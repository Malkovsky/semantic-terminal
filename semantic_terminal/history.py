"""Persist and recall the last generated command."""

from __future__ import annotations

from pathlib import Path

DATA_DIR = Path.home() / ".local" / "share" / "semantic-terminal"
LAST_COMMAND_FILE = DATA_DIR / "last_command"


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
