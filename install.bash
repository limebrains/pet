#!/usr/bin/env bash

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

curl -fsSL https://github.com/dmydlo/pet/archive/master.zip -o pet.zip
if [ ! -f pet.zip ]; then
    printf "\n\e[1;31mInstallation unsuccessful due to failed download\e[0m\n"
    return 1
fi
unzip -o pet.zip
if [ ! -d "pet-master" ]; then
    printf "\n\e[1;31mInstallation unsuccessful due to failed unzip\e[0m\n"
    return 1
fi
pip install -e pet-master/
printf "\n------------------------\n-Installing rest of pet-\n------------------------\n"
if [ "$USER" == 'root' ]; then
    printf "\n\n\e[1;31mWarning (used as root): During first run use\npet recreate\e[0m\n"
else
    python 'pet-master/pet/cli.py' 'recreate'
fi
printf "\n------------------------\n-auto-completion deploy-\n------------------------\n"
printf "\n\e[1;33mAuto-completion requires sudo\e[0m\n"
if [ "$USER" == 'root' ]; then
    sudo python 'pet-master/pet/cli.py' 'deploy'
else
    printf "\n\e[1;33mNeeds sudo - use 'pet deploy'\e[0m\n"
fi
printf "\n\e[1;32mInstallation completed\e[0m\n"
