from subprocess import Popen
import os
import signal
import shutil
from exceptions import NameAlreadyTaken, NameNotFound, ProjectActivated


PET_FOLDER = os.environ.get('PET_FOLDER', os.path.join(os.path.expanduser("~"), ".pet/"))


def create_projects_root():
    os.makedirs(os.path.join(PET_FOLDER, "projects"))


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

        if not os.path.exists(os.path.join(get_projects_root(), name)):
            raise NameNotFound("{0} - project not found".format(name))
        if os.path.isfile(os.path.join(get_projects_root(), name, "_lock")):
            raise ProjectActivated("{0} - project already activated".format(name))
        self.filepath = os.path.join(get_projects_root(), name, "_lock")

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
        Popen(["./boot.sh", name, os.path.join(get_projects_root(), name)]).communicate(input)


def project_exist(name):
    """checks existence of project"""
    return os.path.exists(os.path.join(get_projects_root(), name))


def task_exist(project, name):
    """checks existence of task"""
    return os.path.exists(os.path.join(get_projects_root(), project, "tasks", name + ".sh"))


def stop():
    """stops project"""
    os.kill(os.getppid(), signal.SIGKILL)


new_project_py_file = '''
import click
import bl


@click.group(chain=True, invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        bl.start('{0}')
'''

new_tasks_file = '''
import click
import bl
'''


def create(name, templates=()):
    """creates new project"""
    projects_root = get_projects_root()
    for template in templates:
        if not project_exist(template):
            raise NameNotFound("{0} - template not found".format(template))
    if not os.path.isfile("./shell_profiles"):
        Popen("./create_shell.sh")
    if not os.path.exists(os.path.join(projects_root, name)):
        os.makedirs(os.path.join(projects_root, name))
    if not os.path.exists(os.path.join(projects_root, name, "tasks")):
        os.makedirs(os.path.join(projects_root, name, "tasks"))

    with open(os.path.join(projects_root, name, name + ".py"), mode='w') as project_file:
        project_file.write(new_project_py_file.format(name))

    with open(os.path.join(projects_root, name, "tasks.py"), mode='w') as tasks_file:
        tasks_file.write(new_tasks_file)

    with open(os.path.join(projects_root, name, "start.sh"), mode='w') as start_file:
        if templates:
            start_file.write("# TEMPLATES\n")
            for template in templates:
                start_file.write("# from template: %s\n" % template)
                template_start_file = open(os.path.join(projects_root, template, "start.sh"))
                start_file.write(template_start_file.read())
                start_file.write("\n")
            start_file.write("# check if correctly imported templates\n")
        else:
            start_file.write('# add here shell code to be executed while entering project\n')
    with open(os.path.join(projects_root, name, "stop.sh"), mode='w') as stop_file:
        if templates:
            stop_file.write("# TEMPLATES\n")
            for template in templates:
                stop_file.write("# from template: %s\n" % template)
                template_stop_file = open(os.path.join(projects_root, template, "stop.sh"))
                stop_file.write(template_stop_file.read())
                stop_file.write("\n")
            stop_file.write("# check if correctly imported templates\n")
        else:
            stop_file.write('# add here shell code to be executed while exiting project\n')
    edit_file(os.path.join(projects_root, name, "start.sh"))
    edit_file(os.path.join(projects_root, name, "stop.sh"))


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
            projects_root = get_projects_root()
            Popen(["/bin/sh", "-c", "echo '#!/bin/sh' > {0}".format(os.path.join(projects_root, project, "tasks",
                                                                                 name + ".sh"))]).communicate(input)
            edit_file(os.path.join(projects_root, project, "tasks", name + ".sh"))
            os.chmod(os.path.join(projects_root, project, "tasks", name + ".sh"), 0o755)
            with open(os.path.join(projects_root, project, "tasks.py"), mode='a') as tasks_file:
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


# TODO: Archiving projects with suffix .old plus restore command
def remove(name):
    """removes project"""
    projects_root = get_projects_root()
    if os.path.exists(os.path.join(projects_root, name)):
        if not os.path.exists(os.path.join(projects_root, name, "_lock")):
            shutil.rmtree(os.path.join(projects_root, name))
        else:
            raise ProjectActivated("{0} - project is active".format(name))
    else:
        raise NameNotFound("{0} - project not found".format(name))


def clean():
    """unlocks all projects"""
    projects_root = get_projects_root()
    for dirname in os.listdir(projects_root):
        if os.path.exists(os.path.join(projects_root, dirname, "_lock")):
            os.remove(os.path.join(projects_root, dirname, "_lock"))


def rename(old, new):
    """renames projects"""
    projects_root = get_projects_root()
    if not os.path.exists(os.path.join(projects_root, old)):
        raise NameNotFound("{0} - project not found".format(old))
    if os.path.exists(os.path.join(projects_root, new)):
        raise NameAlreadyTaken("{0} - new name already taken".format(new))
    os.rename(os.path.join(projects_root, old), os.path.join(projects_root, new))


def edit_project(name):
    """edits project start&stop files"""
    projects_root = get_projects_root()
    if name in print_list():
        edit_file(os.path.join(projects_root, name, "start.sh"))
        edit_file(os.path.join(projects_root, name, "stop.sh"))
    else:
        raise NameNotFound("{0} - project not found".format(name))


def run_task(project, task, active, args=()):
    """executes task in correct project"""
    if task_exist(project, task):
        if active == project:
            popen_args = [os.path.join(get_projects_root(), project, "tasks", task + ".sh")]
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
        edit_file(os.path.join(get_projects_root(), project, "tasks", task + ".sh"))
    else:
        raise NameNotFound("{0} - task not found".format(task))
