#!/usr/bin/env bash
_pet()
{
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="archive clean edit init list register remove rename restore run -v --version --help "
    if [ -z "$PET_FOLDER" ]; then
        PET_FOLDER="${HOME}/.pet"
    else
        if [ "${PET_FOLDER:0:1}" == "~" ]; then
            PET_FOLDER="${HOME}${PET_FOLDER:1}"
        fi
        if [ "${PET_FOLDER: -1}" == "/" ]; then
            PET_FOLDER="${PET_FOLDER:0:${#PET_FOLDER}-1}"
        fi
    fi
    projects=$(/bin/ls "$PET_FOLDER/projects/" | cut -d "/" -f 1)
    if [ -z "$PET_ACTIVE_PROJECT" ]; then
        opts="${opts}"
    else
        opts="${opts} stop task "
    fi
    opts=" ${opts} ${projects} "
    first="${COMP_WORDS[1]}"
    count="${#COMP_WORDS[@]}"
    if [ ${count} == 2 ]; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    elif [ ${count} == 3 ]; then
        case $prev in archive|run)
            COMPREPLY=( $(compgen -W "${projects}" -- ${cur}) )
            return 0
        esac
        case $prev in list)
            COMPREPLY=( $(compgen -W "-t -o --tree" -- ${cur}) )
            return 0
        esac
        case $prev in restore)
            archived=$(/bin/ls "$PET_FOLDER/archive" | sed s:\.[^./]*$::)
            COMPREPLY=( $(compgen -W "${archived}" -- ${cur}) )
            return 0
        esac
        if [ -z "$PET_ACTIVE_PROJECT" ]; then
            case $prev in edit|remove|rename)
                COMPREPLY=( $(compgen -W "${projects}" -- ${cur}) )
                return 0
            esac
        else
            case $prev in edit|remove|rename)
                tasks=$(/bin/ls "$PET_FOLDER/projects/$PET_ACTIVE_PROJECT/tasks" | cut -d "." -f 1)
                COMPREPLY=( $(compgen -W "${tasks}" -- ${cur}) )
                return 0
            esac
        fi
    elif [ ${count} == 4 ]; then
        case $first in run)
            if [ -z "$PET_ACTIVE_PROJECT" ]; then
                tasks=$(/bin/ls "$PET_FOLDER/projects/${COMP_WORDS[2]}/tasks" | cut -d "." -f 1)
                COMPREPLY=( $(compgen -W "${tasks}" -- ${cur}) )
                return 0
            fi
        esac
    fi
}
complete -F _pet pet
