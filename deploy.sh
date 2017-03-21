#!/usr/bin/env bash
# THIS IS ONLY FOR BASH... LINUX... U MNIE DZIALA!
 if [ -d '/etc/bash_completion.d' ]; then
            bash_completions='/etc/bash_completion.d'
        else
            bash_completions="$HOME/.bash_completion"
fi

if [ bash_completions == "$HOME/.bash_completion" ]; then
        echo ". /home/dawid/PycharmProjects/pet/complete.bash" >> "$bash_completions"
    else
        yes | echo ". /home/dawid/PycharmProjects/pet/complete.bash" > "$bash_completions/prm"
fi
