import os
from subprocess import Popen

from pet.utils import makedirs

PET_INSTALL_FOLDER = os.path.dirname(os.path.realpath(__file__))
PET_FOLDER = os.environ.get('PET_FOLDER', os.path.join(os.path.expanduser("~"), ".pet/"))


def create_folders():
    makedirs(path=os.path.join(PET_FOLDER, "projects"), exists_ok=True)
    makedirs(path=os.path.join(PET_FOLDER, "archive"), exists_ok=True)
    makedirs(path=os.path.join(PET_FOLDER, "templates", "projects"), exists_ok=True)
    makedirs(path=os.path.join(PET_FOLDER, "templates", "tasks"), exists_ok=True)


def create_active_projects_file():
    Popen(["/bin/sh", "-c", "touch {0}".format(os.path.join(PET_INSTALL_FOLDER, "active_projects"))])


def main():
    create_folders()
    create_active_projects_file()

if __name__ == '__main__':
    main()
