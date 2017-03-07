from subprocess import Popen
import os
import signal
import shutil


class File():

    def __init__(self, filename, mode):
        self.filename = filename
        self.mode = mode

    def __enter__(self):
        self.open_file = open(self.filename, self.mode)

    def __exit__(self, *args):
        self.open_file.close()
        os.remove(self.filename)


def start(name):
    """starts new project"""
    if os.path.exists("./projects/%s" % name):
        if not os.path.isfile("./projects/%s/_lock" % name):
            lock = File(filename="./projects/%s/_lock" % name, mode='w')
            lock.__enter__()
            if not os.path.isfile("./shell_profiles"):
                Popen("./create_shell.sh")
            Popen(["./start.sh", name, "./projects/%s" % name]).communicate(input)
            lock.__exit__()
        else:
            return "project already activated"
    else:
        return "project not found"


def stop():
    """stops project"""
    os.kill(os.getppid(), signal.SIGKILL)


def create(name, templates=None):
    """creates new project"""
    if not os.path.exists("./projects/%s" % name):
        os.makedirs("./projects/%s" % name)
    Popen(["./create.sh", "./projects/%s" % name]).communicate(input)


def list():
    """lists all projects"""
    projects = os.listdir('./projects/')
    if projects:
        return "\n".join(projects)


def remove(name):
    """removes project"""
    shutil.rmtree("./projects/%s" % name)
