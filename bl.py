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


def check_if_project_exist(name):
    return os.path.exists("./projects/%s" % name)


def stop():
    """stops project"""
    os.kill(os.getppid(), signal.SIGKILL)


def create(name, templates=()):
    """creates new project"""
    if not os.path.exists("./projects/%s" % name):
        os.makedirs("./projects/%s" % name)
    create_args = ["./create.sh", "./projects/%s" % name]
    for template in templates:
        if not check_if_project_exist(template):
            raise Exception("template: '%s' not found" % template)
        create_args.append(template)
    Popen(create_args).communicate(input)


def print_list(tasks=()):
    """lists all projects"""
    projects = os.listdir('./projects/')
    if projects:
        return "\n".join(projects)


def remove(name):
    """removes project"""
    if os.path.exists("./projects/%s" % name):
        shutil.rmtree("./projects/%s" % name)
    else:
        raise Exception("project not found")


def clean_up():
    """unlocks all projects"""
    for dirname in os.listdir("./projects"):
        if os.path.exists("./projects/%s/_lock" % dirname):
            os.remove("./projects/%s/_lock" % dirname)


def rename(old, new):
    """renames projects"""
    if not os.path.exists("./projects/%s" % old):
        raise Exception("project not found")
    if os.path.exists("./projects/%s" % new):
        raise Exception("new name already taken")
    os.rename("./projects/%s" % old, "./projects/%s" % new)


def edit_project(name):
    if name in print_list():
        Popen(["./edit_project.sh", "./projects/%s" % name]).communicate(input)
    else:
        raise Exception("project not found")


def edit_task(name):
    pass
