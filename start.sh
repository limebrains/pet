#!/bin/sh

if [ "$SHELL" = "/bin/bash" ]; then
    echo "source ~/.bashrc" > $2/tmp_bashrc
    echo "source ~/.profile" >> $2/tmp_bashrc
    echo "pet_project_name=$1" >> $2/tmp_bashrc
    echo "source $2/project_start" >> $2/tmp_bashrc
    echo "PS1=\"[$1] \$PS1\"" >> $2/tmp_bashrc
    #bash other
    #$SHELL --init-file $2
    $SHELL --rcfile $2/tmp_bashrc
    $SHELL $2/project_stop
elif [ "$SHELL" = "/bin/zsh" ]; then
    if [ "$ZDOTDIR" ]; then
        echo "source $ZDOTDIR/.zshrc" > $2/.zshrc
    else
        echo "source $HOME/.zshrc" > $2/.zshrc
    fi
    echo "pet_project_name=$1" >> $2/.zshrc
    echo "source $2/project_start" >> $2/.zshrc
    echo "PS1=\"[$1] \$PS1\"" >> $2/.zshrc
    #zsh other
    ZDOTDIR=$2 $SHELL
    $SHELL $2/project_stop
else
    echo 'havent found correct $SHELL (/bin/bash, /bin/zsh)'
fi
