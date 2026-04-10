# Semantic Terminal: Current State

## Project Snapshot

- Project: `semantic-terminal` CLI (`sem`)
- Purpose: translate natural-language requests into shell commands using an OpenAI-compatible API
- Language/runtime: Python 3.10+
- Current core line count, we want to keep it low:
  - `semantic_terminal/*.py`: 744 lines

## Runtime State

- Runtime dependencies: stdlib-only (`pyproject.toml` has `dependencies = []`).
- API transport: OpenAI-compatible HTTP calls via `urllib.request` + `json`.
- Request headers: `Content-Type`, `Accept`, `Authorization`, `User-Agent`.
- Config precedence:
  1. `SEM_API_KEY`, `SEM_API_BASE`, `SEM_MODEL`
  2. config file (`~/.config/semantic-terminal/config.json`)
  3. built-in defaults
- History files:
  - `last_command` for replay (`sem !`, `sem -r` without description)
  - `last_interaction.json` for inspect mode (`sem ?`)
- Verbose mode (`-v`/`--verbose`): one API request returns explanation + command.
- Version flag: `-V` / `--version`.

## CLI Modes

- `sem <description>`: generate command
- `sem -r <description>`: generate and execute
- `sem -r`: execute last generated command
- `sem -v <description>` / `sem --verbose <description>`: explanation + final raw command line
- `sem -V` / `sem --version`: show version
- `sem !`: execute last generated command
- `sem ?`: show last request-command pair
- `sem config`, `sem config show`, `sem config set ...`: configuration management
- `sem-setup [--shell auto|bash|zsh|powershell]`: install wrappers and persist profile sourcing

## Shell Wrappers

- Wrapper templates ship as package assets:
  - `semantic_terminal/assets/sem-wrapper.sh` (Bash/Zsh)
  - `semantic_terminal/assets/sem-wrapper.ps1` (PowerShell)
- Persistent installer flow:
  - copies wrapper templates into `~/.local/share/semantic-terminal/`
  - updates target shell profile with one managed source block (idempotent)
  - supports `bash`, `zsh`, and `powershell`
- Public wrapper command:
  - `sem-run`: run last saved command in current shell, or generate/parse/run from description in current shell
- Wrapper parsing contract:
  - accepts non-verbose output (`$ <command>`) and verbose output (last non-empty line)
  - strips optional leading `$ ` before execution

## Implementation Notes

- AI transport is centralized in `_post_chat_completion(...)`.
- Standard command mode uses `generate_command(...)`.
- Verbose mode uses `generate_verbose_command(...)`.
- History write flow stores both:
  - `last_command` for fast replay
  - `last_interaction.json` for inspect mode

## Test and Benchmark Commands

- Deterministic tests (offline):
  - `python -m unittest discover -s tests -p "test_*.py" -v`
- Optional live query tests (requires configured backend):
  - `SEM_TEST_LIVE=1 python -m unittest tests.test_live_queries -v`
- Backend latency benchmark runner:
  - `python benchmarks/latency.py --profiles benchmarks/backends.json --queries benchmarks/queries.json --iterations 5 --warmup 1 --output benchmarks/results/latest.json`
