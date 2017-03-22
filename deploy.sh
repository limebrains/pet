#!/usr/bin/env bash
if [ -z $1 ]; then
    if [ $(echo "$SHELL" | grep "bash") ]; then

        if [ -d '/etc/bash_completion.d' ]; then
                bash_completions='/etc/bash_completion.d'
            else
                bash_completions="$HOME/.bash_completion"
        fi

        if [ "$bash_completions" == "$HOME/.bash_completion" ]; then
                echo ". $1/complete.bash" >> "$bash_completions"
            else
                echo ". $1/complete.bash" > "$bash_completions/prm"
        fi


    elif [ $(echo $SHELL | grep "zsh") ]; then
        echo "zsh completion in progress"
    else
        echo "Shell $SHELL is not supported"
    fi
fi

