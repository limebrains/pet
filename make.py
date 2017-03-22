import os
from bl import create_shell


PET_INSTALL_FOLDER = os.path.dirname(os.path.realpath(__file__))
PET_FOLDER = os.environ.get('PET_FOLDER', os.path.join(os.path.expanduser("~"), ".pet/"))


def create_folders():
    if not os.path.exists(os.path.join(PET_FOLDER, "projects")):
        os.makedirs(os.path.join(PET_FOLDER, "projects"))
    if not os.path.exists(os.path.join(PET_FOLDER, "archive")):
        os.makedirs(os.path.join(PET_FOLDER, "archive"))


if __name__ == '__main__':
    create_folders()
    create_shell()
