"""Persistent shell wrapper setup for ``sem-run``."""

from __future__ import annotations

import argparse
import os
import platform
from importlib import resources
from pathlib import Path

START_MARKER = "# >>> semantic-terminal wrappers >>>"
END_MARKER = "# <<< semantic-terminal wrappers <<<"
INSTALL_DIR = Path.home() / ".local" / "share" / "semantic-terminal"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sem-setup",
        description=(
            "Install and persist sem-run shell wrappers across sessions."
        ),
    )
    parser.add_argument(
        "--shell",
        default="auto",
        choices=("auto", "bash", "zsh", "powershell"),
        help="Target shell (default: auto).",
    )
    return parser


def _detect_shell() -> str | None:
    shell_env = os.environ.get("SHELL", "").strip().lower()
    if shell_env:
        shell_name = Path(shell_env).name
        if "zsh" in shell_name:
            return "zsh"
        if "bash" in shell_name:
            return "bash"
        if "pwsh" in shell_name or "powershell" in shell_name:
            return "powershell"

    if platform.system() == "Windows":
        return "powershell"

    return None


def _resolve_shell(requested: str) -> str:
    if requested != "auto":
        return requested

    detected = _detect_shell()
    if detected is None:
        raise SystemExit(
            "Error: Could not detect shell. "
            "Use --shell with one of: bash, zsh, powershell"
        )

    return detected


def _wrapper_filename(shell_name: str) -> str:
    return "sem-wrapper.ps1" if shell_name == "powershell" else "sem-wrapper.sh"


def _load_template(filename: str) -> str:
    try:
        asset = resources.files("semantic_terminal").joinpath("assets", filename)
        return asset.read_text(encoding="utf-8")
    except (AttributeError, FileNotFoundError, ModuleNotFoundError):
        pass

    repo_fallback = Path(__file__).resolve().parent.parent / "scripts" / filename
    if repo_fallback.is_file():
        return repo_fallback.read_text(encoding="utf-8")

    raise SystemExit(f"Error: Wrapper template '{filename}' was not found.")


def _profile_path(shell_name: str) -> Path:
    if shell_name == "bash":
        return Path.home() / ".bashrc"
    if shell_name == "zsh":
        return Path.home() / ".zshrc"
    if shell_name == "powershell":
        if platform.system() == "Windows":
            return (
                Path.home()
                / "Documents"
                / "PowerShell"
                / "Microsoft.PowerShell_profile.ps1"
            )
        return Path.home() / ".config" / "powershell" / "Microsoft.PowerShell_profile.ps1"
    raise SystemExit(f"Error: Unsupported shell: {shell_name}")


def _profile_source_line(shell_name: str) -> str:
    if shell_name == "powershell":
        return '. "$HOME/.local/share/semantic-terminal/sem-wrapper.ps1"'
    return 'source "$HOME/.local/share/semantic-terminal/sem-wrapper.sh"'


def _strip_managed_block(lines: list[str]) -> list[str]:
    cleaned: list[str] = []
    index = 0

    while index < len(lines):
        if lines[index].strip() == START_MARKER:
            end_index = index + 1
            while end_index < len(lines) and lines[end_index].strip() != END_MARKER:
                end_index += 1

            if end_index >= len(lines):
                cleaned.append(lines[index])
                index += 1
                continue

            index = end_index + 1
            continue
        cleaned.append(lines[index])
        index += 1

    return cleaned


def _strip_legacy_wrapper_lines(lines: list[str], shell_name: str) -> list[str]:
    cleaned: list[str] = []

    for line in lines:
        stripped = line.strip()

        if shell_name in ("bash", "zsh"):
            if "sem-wrapper.sh" in stripped and (
                stripped.startswith("source ") or stripped.startswith(". ")
            ):
                continue
        elif shell_name == "powershell":
            if "sem-wrapper.ps1" in stripped and stripped.startswith(". "):
                continue

        cleaned.append(line)

    return cleaned


def _merge_profile_text(existing_text: str, shell_name: str) -> str:
    newline = "\r\n" if "\r\n" in existing_text else "\n"
    lines = existing_text.replace("\r\n", "\n").split("\n")
    if lines and lines[-1] == "":
        lines.pop()

    lines = _strip_managed_block(lines)
    lines = _strip_legacy_wrapper_lines(lines, shell_name)

    while lines and not lines[-1].strip():
        lines.pop()

    managed_block = [START_MARKER, _profile_source_line(shell_name), END_MARKER]

    if lines:
        lines.append("")
    lines.extend(managed_block)

    merged = "\n".join(lines) + "\n"
    if newline == "\r\n":
        return merged.replace("\n", "\r\n")
    return merged


def _install_wrapper(shell_name: str) -> Path:
    filename = _wrapper_filename(shell_name)
    template = _load_template(filename)

    INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    target = INSTALL_DIR / filename
    target.write_text(template.rstrip("\n") + "\n", encoding="utf-8")

    return target


def _update_profile(shell_name: str) -> Path:
    profile = _profile_path(shell_name)
    profile.parent.mkdir(parents=True, exist_ok=True)

    existing = profile.read_text(encoding="utf-8") if profile.is_file() else ""
    updated = _merge_profile_text(existing, shell_name)
    profile.write_text(updated, encoding="utf-8")

    return profile


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    shell_name = _resolve_shell(args.shell)
    wrapper_path = _install_wrapper(shell_name)
    profile_path = _update_profile(shell_name)

    print(f"Installed wrapper: {wrapper_path}")
    print(f"Updated profile: {profile_path}")

    if shell_name == "powershell":
        print("Activate now: . $PROFILE")
        print(
            "If profile loading is blocked, run: "
            "Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned"
        )
    else:
        print(f"Activate now: source {profile_path}")
