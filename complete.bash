#!/usr/bin/env bash
_pet()
{
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="clean create edit init list register remove rename restore start stop task"
    first="${COMP_WORDS[1]}"
    count="${#COMP_WORDS[@]}"
    if [ ${count} == 2 ]; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi

}
complete -F _pet pet
