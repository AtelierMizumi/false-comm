#!/usr/bin/env bash
# ==============================================================================
# Generate shell completions for bash, zsh, and fish
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
COMPLETIONS_DIR="${REPO_ROOT}/packaging/completions"

mkdir -p "${COMPLETIONS_DIR}"

echo "==> Generating shell completion scripts..."

# Bash completion
cat << 'EOF' > "${COMPLETIONS_DIR}/bash"
# bash completion for false-comm / fc

_false_comm_completion() {
    local IFS=$'\n'
    local response

    response=$(env COMP_WORDS="${COMP_WORDS[*]}" COMP_CWORD=$COMP_CWORD _FALSE_COMM_COMPLETE=complete-bash false-comm 2>/dev/null)

    for completion in $response; do
        IFS=',' read type value description <<< "$completion"
        if [ "$type" = "dir" ]; then
            COMPREPLY=()
            compopt -o dirnames
        elif [ "$type" = "file" ]; then
            COMPREPLY=()
            compopt -o default
        elif [ "$type" = "plain" ]; then
            COMPREPLY+=("$value")
        fi
    done
}

complete -o default -F _false_comm_completion false-comm
complete -o default -F _false_comm_completion fc
EOF

# Zsh completion
cat << 'EOF' > "${COMPLETIONS_DIR}/zsh"
#compdef false-comm fc

_false_comm_zsh() {
    local -a completions
    local -a completions_with_descriptions
    local response
    (( ! $+commands[false-comm] )) && return 1

    response=("${(@f)$(env COMP_WORDS="${words[*]}" COMP_CWORD=$((CURRENT-1)) _FALSE_COMM_COMPLETE=complete-zsh false-comm 2>/dev/null)}")

    for key descr in ${(kv)response}; do
        if [[ -n "$descr" ]]; then
            completions_with_descriptions+=("${key}:${descr}")
        else
            completions+=("${key}")
        fi
    done

    if [ -n "$completions_with_descriptions" ]; then
        _describe -V unsorted completions_with_descriptions -U
    fi

    if [ -n "$completions" ]; then
        compadd -U -V unsorted -a completions
    fi
}

compdef _false_comm_zsh false-comm fc
EOF

# Fish completion
cat << 'EOF' > "${COMPLETIONS_DIR}/fish"
# fish completion for false-comm / fc

function __complete_false_comm
    set -lx COMP_WORDS (commandline -o)
    set -lx COMP_CWORD (math (count $COMP_WORDS) - 1)
    set -lx _FALSE_COMM_COMPLETE complete-fish
    false-comm 2>/dev/null
end

complete -c false-comm -f -a '(__complete_false_comm)'
complete -c fc -f -a '(__complete_false_comm)'
EOF

echo "✔ Shell completions generated in ${COMPLETIONS_DIR}: bash, zsh, fish"
