#!/bin/sh

add_project () {
    echo "source ./shell_profiles" > $2/$3
    echo "pet_project_name=$1" >> $2/$3
    echo "source $2/project_start" >> $2/$3
    echo "PS1=\"[$1] \$PS1\"" >> $2/$3
}

stop_project () {
    $SHELL $1/project_stop
    rm $1/_lock
}

if [ "$SHELL" = "/bin/bash" ]; then
    add_project $1 $2 tmp_bashrc
    #bash other
    #$SHELL --init-file $2/tmp_bashrc
    $SHELL --rcfile $2/tmp_bashrc
    stop_project $2

elif [ "$SHELL" = "/bin/zsh" ]; then
    add_project $1 $2 .zshrc
    ZDOTDIR=$2 $SHELL
    stop_project $2
else
    echo 'havent found correct $SHELL (/bin/bash, /bin/zsh)'
fi
