#!/bin/sh

if [ "$SHELL" = "/bin/bash" ]; then
    "" > shell_profiles
    if [ -f ~/.bashrc ]; then
        echo "source ~/.bashrc" >> shell_profiles
    fi
    if [ -f ~/.profile ]; then
        echo "source ~/.profile" >> shell_profiles
    fi
    if [ -f ~/.bash_profile ]; then
        echo "source ~/.bash_profile" >> shell_profiles
    fi
elif [ "$SHELL" = "/bin/zsh" ]; then
    if [ "$ZDOTDIR" ]; then
        echo "source $ZDOTDIR/.zshrc" > shell_profiles
    else
        echo "source $HOME/.zshrc" > shell_profiles
    fi
else
    echo 'havent found correct $SHELL (/bin/bash, /bin/zsh)'
fi
