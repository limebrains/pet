from subprocess import Popen
import os
from bl import create_shell


PET_INSTALL_FOLDER = os.path.dirname(os.path.realpath(__file__))
PET_FOLDER = os.environ.get('PET_FOLDER', os.path.join(os.path.expanduser("~"), ".pet/"))


def create_folders():
    if not os.path.exists(os.path.join(PET_FOLDER, "projects")):
        os.makedirs(os.path.join(PET_FOLDER, "projects"))
    if not os.path.exists(os.path.join(PET_FOLDER, "archive")):
        os.makedirs(os.path.join(PET_FOLDER, "archive"))


# TODO: this is not needed for now
def get_shell_type():
    if os.environ.get('SHELL', "").find('bash') != -1:
        return "bash"
    elif os.environ.get('SHELL', "").find('zsh') != -1:
        return "zsh"


def deploy_autocomplete():
    Popen([os.path.join(PET_INSTALL_FOLDER, "deploy.sh"), PET_INSTALL_FOLDER])


if __name__ == '__main__':
    deploy_autocomplete()
    create_folders()
    create_shell()
