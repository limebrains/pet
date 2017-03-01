#!/bin/sh

if [ "$SHELL" = "/bin/bash" ]; then
    echo "source ~/.bashrc" > $4/tmp_bashrc
    echo "source ~/.profile" >> $4/tmp_bashrc
    echo "pet_project_name=$2" >> $4/tmp_bashrc
    echo "source $1" >> $4/tmp_bashrc
    #bash other
    #$SHELL --init-file $3
    $SHELL --rcfile $4/tmp_bashrc
# TO TEST!
elif [ "$SHELL" = "/bin/zsh" ]; then
    if [ "$ZDOTDIR" ]; then
        echo "source $ZDOTDIR/.zshrc" > $4/.zshrc
    else
        echo "source $HOME/.zshrc" > $4/.zshrc
    fi
    echo "pet_project_name=$2" >> $4/.zshrc
    echo "source $1" >> $4/.zshrc
    #zsh other
    ZDOTDIR=$4 $SHELL
else
    echo 'havent found correct $SHELL (/bin/bash, /bin/zsh)'
fi






