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


function create_folders(){
printf "\n------------------------\n----Creating folders----\n------------------------\n"
mkdir -p "$PET_FOLDER/projects"
mkdir -p "$PET_FOLDER/archive"
mkdir -p "$PET_FOLDER/templates/projects"
mkdir -p "$PET_FOLDER/templates/tasks"
printf "\n------------------------\n-----Creating files-----\n------------------------\n"
touch "$PET_FOLDER/active_projects"
echo "EDITOR==$EDITOR" > "$PET_FOLDER/config"
}

curl -fsSL https://github.com/dmydlo/pet/archive/master.zip -o pet.zip
if [ ! -f pet.zip ]; then
    printf "\n\e[1;31mInstallation unsuccessful due to failed download\e[0m\n"
    return 1
fi
unzip pet.zip
if [ ! -d "pet-master" ]; then
    printf "\n\e[1;31mInstallation unsuccessful due to failed unzip\e[0m\n"
    return 1
fi
pip install -e pet-master/
printf "\n------------------------\n-Installing rest of pet-\n------------------------\n"
if [ "$USER" == 'root' ]; then
    printf "\n\n\e[1;31mWarning (used as root): During first run use\npet recreate\e[0m\n"
else
    create_folders
fi
printf "\n------------------------\n-auto-completion deploy-\n------------------------\n"
printf "\n\e[1;33mAuto-completion requires sudo\e[0m\n"
sudo bash "$(pwd)/pet-master/pet/deploy"
printf "\n\e[1;32mInstallation completed\e[0m\n"
