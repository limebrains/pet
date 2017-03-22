#!/usr/bin/env bash
# TAKES $1 PET_INSTALL_FOLDER
# THIS IS ONLY FOR BASH... LINUX... U MNIE DZIALA!
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
