from subprocess import Popen
import os
import signal
import shutil


class ProjectLock(object):

    def __init__(self, name):

        if not os.path.exists("./projects/%s" % name):
            raise Exception("project not found")
        if os.path.isfile("./projects/%s/_lock" % name):
            raise Exception("project already activated")
        self.filepath = "./projects/%s/_lock" % name

    def __enter__(self):
        self.open_file = open(self.filepath, "w")

    def __exit__(self, *args):
        self.open_file.close()
        os.remove(self.filepath)


def start(name):
    """starts new project"""
    with ProjectLock(name=name):
        if not os.path.isfile("./shell_profiles"):
            Popen("./create_shell.sh")
        Popen(["./start.sh", name, "./projects/%s" % name]).communicate(input)


def stop():
    """stops project"""
    os.kill(os.getppid(), signal.SIGKILL)


def create(name, templates=[]):
    """creates new project"""
    if not os.path.exists("./projects/%s" % name):
        os.makedirs("./projects/%s" % name)
    create_args = ["./create.sh", "./projects/%s" % name]
    for template in templates:
        if not os.path.exists("./projects/%s" % name):
            return "template: '%s' not found" % template
        create_args.append(template)
    Popen(create_args).communicate(input)


def list():
    """lists all projects"""
    projects = os.listdir('./projects/')
    if projects:
        return "\n".join(projects)


def remove(name):
    """removes project"""
    if os.path.exists("./projects/%s" % name):
        shutil.rmtree("./projects/%s" % name)
    else:
        return "project not found"


def clean_up():
    for dirname in os.listdir("./projects"):
        if os.path.exists("./projects/%s/_lock"):
            os.remove("./projects/%s/_lock")
