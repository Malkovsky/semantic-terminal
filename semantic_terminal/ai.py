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

_EXPLAIN_SYSTEM_PROMPT = """\
You are a command-line assistant. The user will describe what they want to do \
in natural language and you must provide both a short explanation and a shell \
command.

Rules:
- Target the user's environment: {platform} ({shell}).
- Keep the explanation in the same natural language as the user's request.
- The explanation must be short and readable: one heading + 3-5 bullet points.
- Cover what the command does, key flags/options/pipes, and caveats/assumptions.
- Return EXACTLY in this machine-readable format:
  <<SEM_EXPLANATION>>
  <explanation block>
  <<SEM_COMMAND>>
  <one shell command only>
- Do NOT use markdown code fences.
- Do NOT include any extra sections or text outside the format above.
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


def _post_chat_completion(
    *,
    config: Config,
    messages: list[dict[str, str]],
    temperature: float = 0,
    max_tokens: int = 512,
) -> str:
    """Call OpenAI-compatible chat completion endpoint and return message text."""
    payload = {
        "model": config.model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
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

    return content


def generate_command(description: str, config: Config) -> str:
    """Call the AI and return the generated command string.

    Raises ``SystemExit`` on unrecoverable API errors.
    """
    system = _SYSTEM_PROMPT.format(
        platform=platform.system(),
        shell=_detect_shell(),
    )

    content = _post_chat_completion(
        config=config,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": description},
        ],
        temperature=0,
        max_tokens=512,
    )

    # Strip markdown code fences if the model ignores instructions
    if content.startswith("```"):
        lines = content.splitlines()
        # Remove first and last fence lines
        lines = [l for l in lines if not l.startswith("```")]
        content = "\n".join(lines).strip()

    return content


def _parse_verbose_response(content: str) -> tuple[str, str]:
    """Parse verbose response into ``(explanation, command)``."""
    marker_expl = "<<SEM_EXPLANATION>>"
    marker_cmd = "<<SEM_COMMAND>>"

    idx_expl = content.find(marker_expl)
    idx_cmd = content.find(marker_cmd)

    if idx_expl != -1 and idx_cmd != -1 and idx_cmd > idx_expl:
        explanation = content[idx_expl + len(marker_expl):idx_cmd].strip()
        command_block = content[idx_cmd + len(marker_cmd):].strip()
    else:
        lines = [line for line in content.splitlines() if line.strip()]
        if len(lines) < 2:
            raise SystemExit("Error: The AI returned an invalid verbose response.")
        explanation = "\n".join(lines[:-1]).strip()
        command_block = lines[-1].strip()

    if command_block.startswith("```"):
        lines = [line for line in command_block.splitlines() if not line.startswith("```")]
        command_block = "\n".join(lines).strip()

    command_lines = [line.strip() for line in command_block.splitlines() if line.strip()]
    if not command_lines:
        raise SystemExit("Error: The AI returned an invalid verbose response.")

    command = command_lines[0]
    if command.startswith("$ "):
        command = command[2:].strip()

    if not explanation or not command:
        raise SystemExit("Error: The AI returned an invalid verbose response.")

    return explanation, command


def generate_verbose_command(description: str, config: Config) -> tuple[str, str]:
    """Generate ``(explanation, command)`` in one API request."""
    system = _EXPLAIN_SYSTEM_PROMPT.format(
        platform=platform.system(),
        shell=_detect_shell(),
    )

    content = _post_chat_completion(
        config=config,
        messages=[
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": description,
            },
        ],
        temperature=0,
        max_tokens=768,
    )

    if content.startswith("```"):
        lines = content.splitlines()
        lines = [l for l in lines if not l.startswith("```")]
        content = "\n".join(lines).strip()

    return _parse_verbose_response(content)
