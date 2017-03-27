import os

# Third party

# Own
from bl import get_shell


PET_INSTALL_FOLDER = os.path.dirname(os.path.realpath(__file__))
PET_FOLDER = os.environ.get('PET_FOLDER', os.path.join(os.path.expanduser("~"), ".pet/"))


def create_folders():
    os.makedirs(os.path.join(PET_FOLDER, "projects"))
    os.makedirs(os.path.join(PET_FOLDER, "archive"))
    os.makedirs(os.path.join(PET_FOLDER, "templates", "projects"))
    os.makedirs(os.path.join(PET_FOLDER, "templates", "tasks"))


if __name__ == '__main__':
    create_folders()
    get_shell().create_shell_profiles()
