#!/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    if [ $(echo "$SHELL" | grep "bash") ]; then

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

    elif [ $(echo "$SHELL" | grep "zsh") ]; then
        echo "zsh completion in progress"
        printf "\n\n\/ During first run use\npet recreate\n"
    else
        echo "Shell $SHELL is not supported"
    fi
