#!/usr/bin/env sh

_sem_history_file="$HOME/.local/share/semantic-terminal/last_command"

sem_run() {
    cmd=""

    if [ "$#" -eq 0 ]; then
        if [ ! -f "$_sem_history_file" ]; then
            printf '%s\n' "Error: No previous command found at $_sem_history_file" >&2
            return 1
        fi
        cmd="$(cat "$_sem_history_file")"
        if [ -z "$cmd" ]; then
            printf '%s\n' "Error: Last command history is empty." >&2
            return 1
        fi
    else
        output="$(sem "$@")"
        status=$?
        if [ -n "$output" ]; then
            printf '%s\n' "$output"
        fi
        if [ "$status" -ne 0 ]; then
            return "$status"
        fi

        while IFS= read -r line; do
            case "$line" in
                *[![:space:]]*) cmd="$line" ;;
            esac
        done <<EOF
$output
EOF

        case "$cmd" in
            '$ '*) cmd=${cmd#\$ } ;;
        esac

        if [ -z "$cmd" ]; then
            printf '%s\n' "Error: Could not parse command from sem output." >&2
            return 1
        fi
    fi

    if [ -n "${BASH_VERSION:-}" ]; then
        history -s -- "$cmd"
    elif [ -n "${ZSH_VERSION:-}" ]; then
        print -s -- "$cmd"
    fi

    eval "$cmd"
}

alias sem-run='sem_run'
