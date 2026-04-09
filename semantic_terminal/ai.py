"""Send a semantic description to an OpenAI-compatible API and get a command."""

from __future__ import annotations

import json
import platform
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from . import __version__
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
    system = _SYSTEM_PROMPT.format(
        platform=platform.system(),
        shell=_detect_shell(),
    )

    payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": description},
        ],
        "temperature": 0,
        "max_tokens": 512,
    }

    endpoint = f"{config.api_base.rstrip('/')}/chat/completions"
    request = Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {config.api_key}",
            "User-Agent": f"semantic-terminal/{__version__}",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=60) as response:
            raw = response.read()
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace").strip()
        detail = f"HTTP {exc.code}"
        if body:
            detail = f"{detail} — {body}"
        raise SystemExit(f"Error: API request failed — {detail}") from exc
    except URLError as exc:
        raise SystemExit(f"Error: API request failed — {exc.reason}") from exc
    except Exception as exc:
        raise SystemExit(f"Error: API request failed — {exc}") from exc

    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise SystemExit(f"Error: API request failed — Invalid JSON response ({exc})") from exc

    content = (
        data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if isinstance(data, dict)
        else ""
    )
    content = str(content or "").strip()
    if not content:
        raise SystemExit("Error: The AI returned an empty response.")

    # Strip markdown code fences if the model ignores instructions
    if content.startswith("```"):
        lines = content.splitlines()
        # Remove first and last fence lines
        lines = [l for l in lines if not l.startswith("```")]
        content = "\n".join(lines).strip()

    return content
