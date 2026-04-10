# Semantic terminal

[![PyPI](https://img.shields.io/pypi/v/semantic-terminal?color=blue&label=pypi)](https://pypi.org/project/semantic-terminal/)
[![Lines of Code](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/Malkovsky/ccbd74061fc9ce8bee110c2479f5c23c/raw/loc-badge.json)](https://github.com/Malkovsky/semantic-terminal)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A single-purpose command-line tool in the Unix tradition: it does one thing and does it well. `sem` translates natural language into shell commands using AI. Only Python core functionality is used, no additional dependencies.

## Install

```
pip install semantic-terminal
```

Requires Python 3.10+.

## Quick start

1. Get a free API key at [console.groq.com](https://console.groq.com) (sposor the project and I'll gladly change default provider option)
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
sem -r / sem !           # Execute the last generated command
sem -v|--verbose <desc>  # Show detailed breakdown + command
sem -V|--version         # Show version
sem ?                    # Show last request + generated command
```

### `sem-run` command (optional)

Command execution via `sem` runs in a subprocess, this creates a problem that executed commands are not stored in a terminal history which might be uncomfortable for many users. Specifically to solve the issue we give additional setup:   

```bash
sem-setup --shell bash|zsh|powershell
```
or run `sem-setup` with no parameters to auto detect terminal. After installation, `sem-run` behaves like `sem -r` but keeps executed commands in terminal history.

Verification:

```bash
# bash/zsh
type sem-run

# PowerShell
Get-Command sem-run
```

If PowerShell blocks profile loading, use:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

## How it works

`sem` sends your description to the configured AI model with a system prompt that instructs it to 
* Either return exactly one shell command or optionally provide a short breakdown of the command
* Take into account your OS and shell.
* If command breakdown is requested via `--verbose`, describe it in the language of the request.

### Examples

```
$ sem "list files sorted by size"
$ ls -lS

$ sem "find processes using port 8080"
$ lsof -i :8080

$ sem "disk usage of current directory, human readable"
$ du -sh .

$ sem "compress all log files in /var/log older than 7 days"
$ find /var/log -name "*.log" -mtime +7 -exec gzip {} \;

$ sem -v покажи 10 последних коммитов деревом
Чтобы показать последние коммиты в виде дерева, вы можете использовать команду git log с опцией --graph. Вот что делает эта команда:
* Показывает последние коммиты в виде дерева, где каждая ветка представлена отдельной линией
* Опция --graph позволяет визуализировать историю коммитов
* Опция -10 ограничивает вывод до 10 последних коммитов
* Команда git log используется для просмотра истории коммитов
git log --graph -10

$ sem -v 使用树显示10个提交
要显示10个提交记录，可以使用git log命令并结合--oneline和--graph选项来以树形结构显示提交历史。以下是关键点：
* git log命令用于显示提交历史
* --oneline选项使每个提交记录只显示一行
* --graph选项使提交历史以树形结构显示
* --all选项显示所有分支的提交记录
* 使用head选项可以限制显示的提交记录数量
git log --graph --oneline --all -10


$ sem -v Mostrar 10 confirmaciones con el árbol
Para mostrar 10 confirmaciones con el árbol, puedes utilizar el comando git log con las opciones --oneline y --graph. Aquí hay algunos puntos clave sobre este comando:
* El comando git log se utiliza para mostrar un registro de confirmaciones.
* La opción --oneline muestra cada confirmación en una sola línea.
* La opción --graph muestra el árbol de confirmaciones.
* La opción -10 limita la salida a las 10 últimas confirmaciones.
* Este comando asume que estás en el directorio raíz de un repositorio git.
git log --oneline --graph -10
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

Any OpenAI-compatible API works.

### Environment variables

Environment variables take precedence over the config file:

| Variable        | Purpose                      |
|-----------------|------------------------------|
| `SEM_API_KEY`   | API key (highest priority)   |
| `SEM_API_BASE`  | API base URL override        |
| `SEM_MODEL`     | Model override               |
