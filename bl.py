from subprocess import Popen
import os
import signal
import shutil
from exceptions import NameAlreadyTaken, NameNotFound, ProjectActivated


# TODO: change for ~/.pet/
PET_FOLDER = os.environ.get('PET_FOLDER', os.path.join(os.path.expanduser("~"), "PycharmProjects/pet"))


def create_projects_root():
    os.makedirs(PET_FOLDER)


def get_projects_root():
    if os.path.exists(PET_FOLDER):
        return os.path.join(PET_FOLDER, "projects")


def get_projects_root_or_create():
    project_root = get_projects_root()
    if not project_root:
        create_projects_root()
        return get_projects_root(), True
    return project_root, False


class ProjectLock(object):

    def __init__(self, name):

        if not os.path.exists("./projects/%s" % name):
            raise NameNotFound("{0} - project not found".format(name))
        if os.path.isfile("./projects/%s/_lock" % name):
            raise ProjectActivated("{0} - project already activated".format(name))
        self.filepath = "./projects/%s/_lock" % name

    def __enter__(self):
        self.open_file = open(self.filepath, "w")

    def __exit__(self, *args):
        self.open_file.close()
        os.remove(self.filepath)


def edit_file(path):
    """edits file using $EDITOR"""
    Popen(["/bin/sh", "-c", "$EDITOR %s" % path]).communicate(input)


def start(name):
    """starts new project"""
    with ProjectLock(name=name):
        Popen(["./boot.sh", name, "./projects/%s" % name]).communicate(input)


def project_exist(name):
    """checks existence of project"""
    return os.path.exists("./projects/%s" % name)


def task_exist(project, name):
    """checks existence of task"""
    return os.path.exists("./projects/%s/tasks/%s.sh" % (project, name))


def stop():
    """stops project"""
    os.kill(os.getppid(), signal.SIGKILL)


new_project_py_file = '''import click
import bl


@click.group(chain=True, invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        bl.start('{0}')
'''

new_tasks_file = '''import click
import bl
'''


def create(name, templates=()):
    """creates new project"""
    for template in templates:
        if not project_exist(template):
            raise NameNotFound("{0} - template not found".format(template))
    if not os.path.isfile("./shell_profiles"):
        Popen("./create_shell.sh")
    if not os.path.exists("./projects/%s" % name):
        os.makedirs("./projects/%s" % name)
    if not os.path.exists("./projects/%s/tasks" % name):
        os.makedirs("./projects/%s/tasks" % name)

    with open("./projects/%s/%s.py" % (name, name), mode='w') as project_file:
        project_file.write(new_project_py_file.format(name))

    with open("./projects/%s/tasks.py" % name, mode='w') as tasks_file:
        tasks_file.write(new_tasks_file)

    with open("./projects/%s/start.sh" % name, mode='w') as start_file:
        if templates:
            start_file.write("# TEMPLATES\n")
            for template in templates:
                start_file.write("# from template: %s\n" % template)
                template_start_file = open("./projects/%s/start.sh" % template)
                start_file.write(template_start_file.read())
                start_file.write("\n")
            start_file.write("# check if correctly imported templates\n")
        else:
            start_file.write('# add here shell code to be executed while entering project\n')
    with open("./projects/%s/stop.sh" % name, mode='w') as stop_file:
        if templates:
            stop_file.write("# TEMPLATES\n")
            for template in templates:
                stop_file.write("# from template: %s\n" % template)
                template_stop_file = open("./projects/%s/stop.sh" % template)
                stop_file.write(template_stop_file.read())
                stop_file.write("\n")
            stop_file.write("# check if correctly imported templates\n")
        else:
            stop_file.write('# add here shell code to be executed while exiting project\n')
    edit_file("./projects/%s/start.sh" % name)
    edit_file("./projects/%s/stop.sh" % name)


new_task = '''

@click.command()
@click.argument('args', nargs=-1)
@click.option('--active', envvar='PET_ACTIVE_PROJECT')
def {0}(active="", args=()):
    \"""{1}""\"
    bl.run_task("{2}", "{3}", active, args)
'''


def create_task(project, name, description):
    """creates task"""
    if project_exist(project):
        if not task_exist(project, name):
            Popen(["/bin/sh", "-c", "echo '#!/bin/sh' > ./projects/%s/tasks/%s.sh" % (project, name)]).communicate(input)
            edit_file("./projects/%s/tasks/%s.sh" % (project, name))
            os.chmod("./projects/%s/tasks/%s.sh" % (project, name), 0o755)
            with open("./projects/%s/tasks.py" % project, mode='a') as tasks_file:
                tasks_file.write(new_task.format(name, description, project, name))
        else:
            raise NameAlreadyTaken("{0} - task already exists".format(name))
    else:
        raise NameNotFound("{0} - project not found".format(project))


def print_list():
    """lists all projects"""
    projects_root = get_projects_root()
    projects = [
        project
        for project in os.listdir(projects_root)
        if os.path.isdir(os.path.join(projects_root, project))
    ]
    if projects:
        return "\n".join(projects)


def remove(name):
    """removes project"""
    if os.path.exists("./projects/%s" % name):
        if not os.path.exists("./projects/%s/_lock" % name):
            shutil.rmtree("./projects/%s" % name)
        else:
            raise ProjectActivated("{0} - project is active".format(name))
    else:
        raise NameNotFound("{0} - project not found".format(name))


def clean():
    """unlocks all projects"""
    for dirname in os.listdir("./projects"):
        if os.path.exists("./projects/%s/_lock" % dirname):
            os.remove("./projects/%s/_lock" % dirname)


def rename(old, new):
    """renames projects"""
    if not os.path.exists("./projects/%s" % old):
        raise NameNotFound("{0} - project not found".format(old))
    if os.path.exists("./projects/%s" % new):
        raise NameAlreadyTaken("{0} - new name already taken".format(new))
    os.rename("./projects/%s" % old, "./projects/%s" % new)


def edit_project(name):
    """edits project start&stop files"""
    if name in print_list():
        edit_file("./projects/%s/start.sh" % name)
        edit_file("./projects/%s/stop.sh" % name)
    else:
        raise NameNotFound("{0} - project not found".format(name))


def run_task(project, task, active, args=()):
    """executes task in correct project"""
    if task_exist(project, task):
        if active == project:
            popen_args = ["./projects/%s/tasks/%s.sh" % (project, task)]
            popen_args.extend(list(args))
            Popen(popen_args)
        else:
            # TODO: run in project if is not already turned on
            pass
    else:
        raise NameNotFound("{0} - task not found".format(task))


def edit_task(project, task):
    """edits task"""
    if task_exist(project, task):
        edit_file("./projects/%s/tasks/%s.sh" % (project, task))
    else:
        raise NameNotFound("{0} - task not found".format(task))
