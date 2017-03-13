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


def edit_file(path):
    Popen(["/bin/sh", "-c", "$EDITOR %s" % path]).communicate(input)


def start(name):
    """starts new project"""
    with ProjectLock(name=name):
        Popen(["./start.sh", name, "./projects/%s" % name]).communicate(input)


def check_if_project_exist(name):
    return os.path.exists("./projects/%s" % name)


def check_if_task_exist(project, name):
    return os.path.exists("./projects/%s/tasks/%s.sh" % (project, name))


def stop():
    """stops project"""
    os.kill(os.getppid(), signal.SIGKILL)


def create(name, templates=()):
    """creates new project"""
    for template in templates:
        if not check_if_project_exist(template):
            raise Exception("template: %s not found" % template)
    if not os.path.isfile("./shell_profiles"):
        Popen("./create_shell.sh")
    if not os.path.exists("./projects/%s" % name):
        os.makedirs("./projects/%s" % name)
    if not os.path.exists("./projects/%s/tasks" % name):
        os.makedirs("./projects/%s/tasks" % name)

    with open("./projects/%s/%s.py" % (name, name), mode='w') as project_file:
        project_file.write("""import click
import bl


@click.group(chain=True, invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        bl.start('%s')
""" % name)

    with open("./projects/%s/project_start" % name, mode='w') as start_file:
        if templates:
            start_file.write("# TEMPLATES\n")
            for template in templates:
                start_file.write("# from template: %s\n" % template)
                template_start_file = open("./projects/%s/project_start" % template)
                start_file.write(template_start_file.read())
                start_file.write("\n")
            start_file.write("# check if correctly imported templates\n")
        else:
            start_file.write('# add here shell code to be executed while entering project\n')
    with open("./projects/%s/project_stop" % name, mode='w') as stop_file:
        if templates:
            stop_file.write("# TEMPLATES\n")
            for template in templates:
                stop_file.write("# from template: %s\n" % template)
                template_stop_file = open("./projects/%s/project_stop" % template)
                stop_file.write(template_stop_file.read())
                stop_file.write("\n")
            stop_file.write("# check if correctly imported templates\n")
        else:
            stop_file.write('# add here shell code to be executed while exiting project\n')
    edit_file("./projects/%s/project_start" % name)
    edit_file("./projects/%s/project_stop" % name)


def create_task(project, name, description):
    if check_if_project_exist(project):
        if not check_if_task_exist(project, name):
            Popen(["/bin/sh", "-c", "echo '#!/bin/sh' > ./projects/%s/tasks/%s.sh" % (project, name)]).communicate(input)
            edit_file("./projects/%s/tasks/%s.sh" % (project, name))
            os.chmod("./projects/%s/tasks/%s.sh" % (project, name), 0o755)
            with open("./projects/%s/%s.py" % (project, project), mode='a') as project_file:
                project_file.write("""

@cli.command()
@click.argument('args', nargs=-1)
def %s(args=()):
    \"""%s""\"
    bl.run_task("%s", "%s", args)
""" % (name, description, project, name))
        else:
            raise Exception("task already exists")
    else:
        raise Exception("project not found")


def print_list():
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
        edit_file("./projects/%s/project_start" % name)
        edit_file("./projects/%s/project_stop" % name)
    else:
        raise Exception("project not found")


def run_task(project, task, args=()):
    if check_if_task_exist(project, task):
        popen_args = ["./projects/%s/tasks/%s.sh" % (project, task)]
        popen_args.extend(list(args))
        Popen(popen_args)
    else:
        raise Exception("task not found")


def edit_task(project, task):
    if check_if_task_exist(project, task):
        edit_file("./projects/%s/tasks/%s.sh" % (project, task))
    else:
        raise Exception("task not found")
