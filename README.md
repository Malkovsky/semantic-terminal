# Semantic terminal

[![PyPI](https://img.shields.io/pypi/v/semantic-terminal?color=blue&label=pypi)](https://pypi.org/project/semantic-terminal/)
[![Lines of Code](https://tokei.rs/b1/github/Malkovsky/semantic-terminal?category=code)](https://github.com/Malkovsky/semantic-terminal)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A single-purpose command-line tool in the Unix tradition: it does one thing and does it well. `sem` translates natural language into shell commands using AI.

Just like `grep` searches, `sed` edits, and `awk` processes text, `sem` translates intent into commands. It fits naturally into a terminal workflow -- describe what you want, get the command, run it.

## Install

```
pip install semantic-terminal
```

Requires Python 3.10+.

## Quick start

1. Get a free API key at [console.groq.com](https://console.groq.com)
2. Run the setup wizard:
   ```
   sem config
   ```
3. Start using it:
   ```
   sem "find all python files larger than 1MB"
   ```

## Usage

```
sem <description>        # Generate a command
sem -r <description>     # Generate and execute
sem !                    # Re-run the last generated command
```

### Examples

```
$ sem "list files sorted by size"
$ ls -lS

$ sem "find processes using port 8080"
$ lsof -i :8080

$ sem -r "disk usage of current directory, human readable"
$ du -sh .
4.2G    .

$ sem "compress all log files in /var/log older than 7 days"
$ find /var/log -name "*.log" -mtime +7 -exec gzip {} \;
```

The generated command targets your OS and shell automatically.

## Configuration

Run the interactive wizard:

```
sem config
```

Or manage individual settings:

```
sem config show                              # View current config
sem config set api_base https://...          # Set API endpoint
sem config set api_key                       # Set API key (hidden prompt)
sem config set model llama-3.3-70b-versatile # Set model
```

### Defaults

| Setting  | Default                              |
|----------|--------------------------------------|
| Provider | [Groq](https://groq.com) (free tier) |
| Model    | `llama-3.3-70b-versatile`            |
| API Base | `https://api.groq.com/openai/v1`     |

Any OpenAI-compatible API works -- just change `api_base` and `model`.

### Environment variables

Environment variables take precedence over the config file:

| Variable        | Purpose                      |
|-----------------|------------------------------|
| `SEM_API_KEY`   | API key (highest priority)   |
| `GROQ_API_KEY`  | Groq API key fallback        |
| `OPENAI_API_KEY`| OpenAI API key fallback      |
| `SEM_API_BASE`  | API base URL override        |
| `SEM_MODEL`     | Model override               |

### Security

- API key is entered via hidden prompt -- never exposed in shell history
- Config file is stored with owner-only permissions (`0600` / user-only ACL)
- `sem config show` masks the API key in output

## How it works

`sem` sends your description to the configured AI model with a system prompt that instructs it to return exactly one shell command targeting your OS and shell. The command is displayed, saved to history for `sem !` recall, and optionally executed with `-r`.

