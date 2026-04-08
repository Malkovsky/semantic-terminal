"""CLI entry point for ``sem``."""

from __future__ import annotations

import argparse
import subprocess
import sys

from . import __version__
from .ai import generate_command
from .config import load_config
from .configure import run_set, run_show, run_wizard
from .history import load_last_command, save_last_command


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sem",
        description="Convert a natural-language description into a terminal command.",
        epilog=(
            "commands:\n"
            '  sem <description>        Generate a command (e.g. sem "list large files")\n'
            "  sem -r <description>     Generate and execute the command\n"
            "  sem !                    Recall and execute the last generated command\n"
            "  sem config               Interactive configuration wizard\n"
            "  sem config show          Show current configuration\n"
            "  sem config set <k> [v]   Set a configuration value"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "description",
        nargs="*",
        metavar="description",
        help='Semantic description, "!", or "config" subcommand.',
    )
    parser.add_argument(
        "-r",
        "--run",
        action="store_true",
        default=False,
        help="Execute the generated command after displaying it.",
    )
    parser.add_argument(
        "-m",
        "--model",
        default=None,
        help="Override the AI model (e.g. gpt-4o, gpt-3.5-turbo).",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def _execute(command: str) -> int:
    """Run *command* in the user's shell and return the exit code."""
    result = subprocess.run(command, shell=True)
    return result.returncode


def _handle_config(tokens: list[str]) -> None:
    """Route ``sem config [show | set <key> [value]]`` subcommands.

    Exits the process when done.
    """
    # sem config  (no subcommand) → interactive wizard
    if not tokens:
        run_wizard()
        raise SystemExit(0)

    sub = tokens[0]

    if sub == "show":
        run_show()
        raise SystemExit(0)

    if sub == "set":
        if len(tokens) < 2:
            raise SystemExit(
                "Usage: sem config set <key> [value]\n"
                "       sem config set api_key        (prompts securely)\n"
                "       sem config set model gpt-4o\n"
                "       sem config set api_base https://..."
            )
        key = tokens[1]
        value = tokens[2] if len(tokens) >= 3 else None
        run_set(key, value)
        raise SystemExit(0)

    raise SystemExit(
        f"Error: Unknown config subcommand '{sub}'.\n"
        "Usage: sem config [show | set <key> [value]]"
    )


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Join the positional tokens back into a single string
    tokens = args.description if args.description else []
    description = " ".join(tokens).strip()

    if not description:
        parser.print_help()
        raise SystemExit(0)

    # --- Config subcommand ---------------------------------------------------
    if tokens[0] == "config":
        _handle_config(tokens[1:])

    # --- Recall mode: `sem !` ------------------------------------------------
    if description == "!":
        last = load_last_command()
        if last is None:
            raise SystemExit("Error: No previous command found.")
        print(f"$ {last}")
        raise SystemExit(_execute(last))

    # --- Normal mode: generate a command -------------------------------------
    config = load_config(model_override=args.model)
    config.validate()

    command = generate_command(description, config)

    # Display the command
    print(f"$ {command}")

    # Persist for later recall with `sem !`
    save_last_command(command)

    # Optionally execute
    if args.run:
        raise SystemExit(_execute(command))
