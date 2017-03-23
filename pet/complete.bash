#!/usr/bin/env bash
_pet()
{
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="archive clean edit init list register remove rename restore"
    projects=" new"
    if [ -z "$PET_ACTIVE_PROJECT" ]; then
        opts="${opts} stop task"
    else
        opts="${opts} run"
    fi
    opts="${opts}${projects}"
    first="${COMP_WORDS[1]}"
    count="${#COMP_WORDS[@]}"
    if [ ${count} == 2 ]; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi

}
complete -F _pet pet
