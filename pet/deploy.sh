#!/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "give name of shell you are using accepting bash/ zsh"
read shell
    if [ $(echo "$shell" | grep "bash") ]; then

        if [ $(uname -s) = "Darwin" ]; then
            if [ -d "$(brew --prefix)/etc/bash_completion.d/" ]; then
                bash_completions="$(brew --prefix)/etc/bash_completion.d"
            fi
        fi

        if [ -z "$bash_completions" ]; then
            if [ -d '/etc/bash_completion.d' ]; then
                    bash_completions='/etc/bash_completion.d'
                else
                    bash_completions="$HOME/.bash_completion"
            fi
        fi

        if [ "$bash_completions" == "$HOME/.bash_completion" ]; then
                echo ". $DIR/complete.bash" >> "$bash_completions"
            else
                echo ". $DIR/complete.bash" > "$bash_completions/pet"
        fi
        printf "\n\n\/ During first run use\npet recreate\n"

    elif [ $(echo "$shell" | grep "zsh") ]; then
        echo "zsh completion in progress"
        printf "\n\n\/ During first run use\npet recreate\n"
    else
        echo "Shell $shell is not supported"
    fi
