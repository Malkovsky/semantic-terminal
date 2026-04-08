"""Send a semantic description to an OpenAI-compatible API and get a command."""

from __future__ import annotations

import platform
import shutil

from openai import OpenAI

from .config import Config

_SYSTEM_PROMPT = """\
You are a command-line assistant. The user will describe what they want to do \
in natural language and you must respond with EXACTLY ONE shell command that \
accomplishes it.

Rules:
- Output ONLY the command. No explanation, no markdown fences, no commentary.
- Target the user's environment: {platform} ({shell}).
- Prefer widely available, standard tools.
- Never produce destructive commands (rm -rf /, format, etc.) unless the user \
  explicitly describes destructive intent.
- If the request is ambiguous, pick the safest reasonable interpretation.
- If the task genuinely cannot be done in a single command, chain with && or \
  pipes as appropriate.
"""


def _detect_shell() -> str:
    """Best-effort detection of the current shell."""
    import os

    shell = os.environ.get("SHELL") or os.environ.get("COMSPEC") or ""
    # Return just the executable name for brevity
    return shell.rsplit("/", 1)[-1].rsplit("\\", 1)[-1] or "unknown"


def generate_command(description: str, config: Config) -> str:
    """Call the AI and return the generated command string.

    Raises ``SystemExit`` on unrecoverable API errors.
    """
    client = OpenAI(api_key=config.api_key, base_url=config.api_base)

    system = _SYSTEM_PROMPT.format(
        platform=platform.system(),
        shell=_detect_shell(),
    )

    try:
        response = client.chat.completions.create(
            model=config.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": description},
            ],
            temperature=0,
            max_tokens=512,
        )
    except Exception as exc:
        raise SystemExit(f"Error: API request failed — {exc}") from exc

    content = (response.choices[0].message.content or "").strip()
    if not content:
        raise SystemExit("Error: The AI returned an empty response.")

    # Strip markdown code fences if the model ignores instructions
    if content.startswith("```"):
        lines = content.splitlines()
        # Remove first and last fence lines
        lines = [l for l in lines if not l.startswith("```")]
        content = "\n".join(lines).strip()

    return content
