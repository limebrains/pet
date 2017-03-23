# Python
import os
import signal
import shutil

from subprocess import Popen, PIPE

# Third party

# Own
from file_templates import (
    new_tasks_file,
    new_project_py_file,
    new_task,
)
from pet_exceptions import PetException, NameAlreadyTaken, NameNotFound, ProjectActivated

# TODO: make tasks not only in .sh


# TODO: templates with tasks and different instance than projects themself


PET_INSTALL_FOLDER = os.path.dirname(os.path.realpath(__file__))
PET_FOLDER = os.environ.get('PET_FOLDER', os.path.join(os.path.expanduser("~"), ".pet/"))
# TODO: refactor V caps
commands = "pet archive clean edit init list register remove rename restore stop task run".split()
BASH_RC_FILENAME = "bashrc"
ZSH_RC_FILENAME = ".zshrc"
# TODO: refactor V
# TODO: refactor V
class GeneralShellMixin:
    def join_path_rc(self):
        return "..."

class Bash(GeneralShellMixin):
    def get_rc_file(self):
        return self.join_path_rc()

class Zsh(GeneralShellMixin):
    def get_rc_file(self):
        pass


SHELL_TO_CLASS = {
    'bash': Bash(),
    'zsh': Zsh(),
}
# TODO: refactor V
EX_PROJECT_NOT_FOUND = "{0} - project not found"
EX_PROJECT_IS_ACTIVE = "{0} - project is active"
EX_PROJECT_EXISTS = "{0} - name already taken"
EX_PROJECT_IN_ARCHIVE = "{0} - name already taken in archive"
EX_TEMPLATE_NOT_FOUND = "{0} - template not found"
EX_TASK_NOT_FOUND = "{0} - task not found"
EX_TASK_ALREADY_EXISTS = "{0}- task already exists"
EX_ISNT_SUPPORTED = "{0} - isn't supported"
SHELL_PROFILES = "shell_profiles"




def get_pet_install_folder():
    return PET_INSTALL_FOLDER


def get_pet_folder():
    return PET_FOLDER


def get_projects_root():
    if os.path.exists(os.path.join(PET_FOLDER, "projects")):
        return os.path.join(PET_FOLDER, "projects")


def get_templates_root():
    if os.path.exists(os.path.join(PET_FOLDER, "templates")):
        return os.path.join(PET_FOLDER, "templates")


def get_archive_root():
    if os.path.exists(os.path.join(PET_FOLDER, "archive")):
        return os.path.join(PET_FOLDER, "archive")


def get_shell_as_type():
    return SHELL_TO_CLASS.get(os.environ.get('SHELL', default=""))


def get_rc_file(project_root):
    if os.path.isfile(os.path.join(project_root, bashrc)):
        return os.path.join(project_root, bashrc)
    elif os.path.isfile(os.path.join(project_root, zshrc)):
        return os.path.join(project_root, zshrc)


def get_rc_type(project_root):
    if os.environ.get('SHELL', "").find('bash') != -1 and os.path.isfile(os.path.join(project_root, bashrc)):
        return bashrc
    elif os.environ.get('SHELL', "").find('zsh') != -1 and os.path.isfile(os.path.join(project_root, zshrc)):
        return zshrc


def make_rc_file(name, project_root, shell):
    contents = "source {0}/shell_profiles\nexport PET_ACTIVE_PROJECT='{1}'\nsource {2}/start.sh\nPS1=\"[{1}] $PS1\"\n" \
               "source {3}\n".format(PET_INSTALL_FOLDER, name, project_root, os.path.join(project_root, "tasks.sh"))
    rc_type = get_shell_as_type()
    if rc_type:
        rc = os.path.join(project_root, rc_type)
        with open(rc, mode='w') as rcfile:
            rcfile.write(contents)
    else:
        raise NameNotFound("{0} - isn't supported or correct file isn't existing".format(shell))


def edit_file(path):
    """edits file using $EDITOR"""
    Popen(["/bin/sh", "-c", "$EDITOR {0}".format(path)]).communicate(input)


def project_exist(name):
    """checks existence of project"""
    return os.path.exists(os.path.join(get_projects_root(), name))


def template_exist(name):
    """checks existence of project"""
    return os.path.exists(os.path.join(get_templates_root(), name))


def task_exist(project, name):
    """checks existence of task"""
    return os.path.exists(os.path.join(get_projects_root(), project, "tasks", name + ".sh"))


def complete_add(project):
    Popen(["/bin/sh", "-c", "sed -i '/projects=/ s/\"$/ {0}\"/' {1}".format(project, os.path.join(
        PET_INSTALL_FOLDER, "complete.bash"))])


def complete_remove(project):
    line_nr = Popen(["/bin/sh", "-c", "grep -n \"projects=\" {0} | cut -d \":\" -f 1".format(
        os.path.join(PET_INSTALL_FOLDER, "complete.bash"))],
                    stdout=PIPE).stdout.read()
    if line_nr:
        line_nr = int(line_nr.decode("utf-8")[:-1])
        Popen(["/bin/sh", "-c", "sed -i '{0}s/{1}//' {2}".format(
            line_nr, " " + project, os.path.join(PET_INSTALL_FOLDER, "complete.bash"))])


def create_shell():
    shell = os.environ.get('SHELL', "")
    if shell.find('bash') != -1:
        with open(os.path.join(PET_INSTALL_FOLDER, 'shell_profiles'), mode='w') as shell_profiles_file:
            if os.path.isfile(os.path.join(os.path.expanduser("~"), '.bashrc')):
                shell_profiles_file.write("source ~/.bashrc\n")
            if os.path.isfile(os.path.join(os.path.expanduser("~"), '.profile')):
                shell_profiles_file.write("source ~/.profile\n")
            if os.path.isfile(os.path.join(os.path.expanduser("~"), '.bash_profile')):
                shell_profiles_file.write("source ~/.bash_profile\n")
    elif shell.find('zsh') != -1:
        if os.environ.get('ZDOTDIR', ""):
            with open(os.path.join(PET_INSTALL_FOLDER, 'shell_profiles'), mode='w') as shell_profiles_file:
                shell_profiles_file.write("source $ZDOTDIR/.zshrc\n")
        else:
            with open(os.path.join(PET_INSTALL_FOLDER, 'shell_profiles'), mode='w') as shell_profiles_file:
                shell_profiles_file.write("source $HOME/.zshrc\n")
    else:
        raise NameNotFound(ex_isnt_supported.format(shell))


class ProjectLock(object):

    def __init__(self, name):

        if not os.path.exists(os.path.join(get_projects_root(), name)):
            raise NameNotFound(ex_project_not_found.format(name))
        self.filepath = os.path.join(get_projects_root(), name, "_lock")

    def __enter__(self):
        self.open_file = open(self.filepath, "w")

    def __exit__(self, *args):
        self.open_file.close()
        os.remove(self.filepath)


class TaskExec(object):

    def __init__(self, project, task, shell, interactive, args=()):

        self.project = project
        self.task = task
        self.project_root = os.path.join(get_projects_root(), project)
        self.args = args
        self.interactive = interactive
        self.shell = shell

    def __enter__(self):
        if self.interactive:
            if self.shell.find('bash') != -1:
                # TODO: refactor V use temp file
                run_path = os.path.join(self.project_root, 'run.bash')
                with open(run_path, mode='w') as run:
                    run.write("#!/usr/bin/env bash\n$SHELL --rcfile <(echo '. {0}; {1}')\n".format(
                        os.path.join(self.project_root, bashrc),
                        os.path.join(self.project_root, "tasks", self.task + ".sh")))
                os.chmod(run_path, 0o755)
                Popen(["/bin/sh", "-c", "{0}\n$SHELL {1}/stop.sh".format(
                    run_path, self.project_root)]).communicate(input)
                os.remove(run_path)
            elif self.shell.find('zsh') != -1:
                # TODO: find a way to make interactive tasks in zsh
                print("it doesn't work in zsh")
            else:
                raise NameNotFound(ex_isnt_supported.format(self.shell))
        else:
            popen_args = [os.path.join(self.project_root, "tasks", self.task + ".sh")]
            popen_args.extend(self.args)
            Popen(popen_args)

    def __exit__(self, *args):
        pass


class ProjectCreator(object):

    def __init__(self, name, templates=()):
        self.projects_root = get_projects_root()
        self.templates_root = get_templates_root()
        self.name = name
        self.project_root = os.path.join(self.projects_root, self.name)
        self.templates = templates
        self.check_name()
        self.check_templates()

    def check_name(self):
        if self.name in print_list():
            raise NameAlreadyTaken(ex_project_exists.format(self.name))
        if self.name in commands:
            raise NameAlreadyTaken("{0} - there is pet command with this name".format(self.name))

    def check_templates(self):
        for template in self.templates:
            if not template_exist(template):
                raise NameNotFound(ex_template_not_found.format(template))

    def create_dirs(self):
        if not os.path.isfile(os.path.join(PET_INSTALL_FOLDER, shell_profiles)):
            create_shell()
        # TODO: refactor V use one call
        if not os.path.exists(self.project_root):
            os.makedirs(self.project_root)
        if not os.path.exists(os.path.join(self.project_root, "tasks")):
            os.makedirs(os.path.join(self.project_root, "tasks"))
        make_rc_file(self.name, self.project_root, os.environ.get('SHELL', ""))

    def create_additional_files(self):
        with open(os.path.join(self.project_root, self.name + ".py"), mode='w') as project_file:
            # TODO: refactor V new project template
            project_file.write(new_project_py_file.format(self.name))
        with open(os.path.join(self.project_root, "tasks.py"), mode='w') as tasks_file:
            # TODO: refactor V task file template?
            tasks_file.write(new_tasks_file)
        with open(os.path.join(self.project_root, "tasks.sh"), mode='w') as tasks_alias_file:
            tasks_alias_file.write("# aliases for your tasks\n")

    # TODO: create_start and stop are redundant

    def create_start(self):
        with open(os.path.join(self.project_root, "start.sh"), mode='w') as start_file:
            if self.templates:
                start_file.write("# TEMPLATES\n")
                for template in self.templates:
                    start_file.write("# from template: {0}\n".format(template))
                    template_start_file = open(os.path.join(self.templates_root, template, "start.sh"))
                    start_file.write(template_start_file.read())
                    start_file.write("\n")
                start_file.write("# check if correctly imported templates\n")
            else:
                start_file.write('# add here shell code to be executed while entering project\n')

    def create_stop(self):
        with open(os.path.join(self.project_root, "stop.sh"), mode='w') as stop_file:
            if self.templates:
                stop_file.write("# TEMPLATES\n")
                for template in self.templates:
                    stop_file.write("# from template: {0}\n".format(template))
                    template_stop_file = open(os.path.join(self.templates_root, template, "stop.sh"))
                    stop_file.write(template_stop_file.read())
                    stop_file.write("\n")
                stop_file.write("# check if correctly imported templates\n")
            else:
                stop_file.write('# add here shell code to be executed while exiting project\n')

    def edit(self):
        edit_file(os.path.join(self.project_root, "start.sh"))
        edit_file(os.path.join(self.project_root, "stop.sh"))

    def create(self):
        self.create_dirs()
        self.create_additional_files()
        self.create_start()
        self.create_stop()
        self.edit()
        complete_add(self.name)


def lockable(check_only=False):
    def _lockable(func):
        def __lockable(name, check_only=check_only, *args, **kwargs):
            print(check_only, name, func, args, kwargs)
            if os.path.isfile(os.path.join(get_projects_root(), name, "_lock")):
                raise ProjectActivated(ex_project_is_active.format(name))
            if not check_only:
                with ProjectLock(name):
                    return func(name, *args, **kwargs)
            else:
                return func(name, *args, **kwargs)
        return __lockable
    return _lockable


@lockable(check_only=False)
def start(name):
    """starts new project"""
    if not os.path.isfile(os.path.join(PET_INSTALL_FOLDER, shell_profiles)):
        create_shell()
    project_root = os.path.join(get_projects_root(), name)
    shell = os.environ.get('SHELL', "")
    make_rc_file(name, project_root, shell)
    if shell.find('bash') != -1:
        Popen(["/bin/sh", "-c", "$SHELL --rcfile {0}\n$SHELL {1}/stop.sh".format(
            os.path.join(project_root, 'bashrc'), project_root)]).communicate(input)
    elif shell.find('zsh') != -1:
        print('I am doing this!')
        Popen(["/bin/sh", "-c", "ZDOTDIR={0} $SHELL\n$SHELL {0}/stop.sh".format(
            project_root)]).communicate(input)
    else:
        raise NameNotFound(ex_isnt_supported.format(shell))


def create(name, templates=()):
    """creates new project"""
    ProjectCreator(name, templates).create()


def register():
    """adds symbolic link to .pet folder in projects"""
    folder = os.getcwd()
    name = os.path.basename(folder)
    if not project_exist(name):
        if (os.path.isfile(os.path.join(folder, name + ".py")) and
                os.path.isfile(os.path.join(folder, "start.sh")) and
                os.path.isfile(os.path.join(folder, "stop.sh")) and
                os.path.isfile(os.path.join(folder, "tasks.py")) and
                os.path.isdir(os.path.join(folder, "tasks"))):
            os.symlink(folder, os.path.join(get_projects_root(), name))
            complete_add(name)
        else:
            raise PetException("Haven't found all 5 files and tasks folder in\n{0}".format(folder))
    else:
        raise NameAlreadyTaken(ex_project_exists.format(name))


def rename_project(old, new):
    """renames projects"""
    projects_root = get_projects_root()
    if not os.path.exists(os.path.join(projects_root, old)):
        raise NameNotFound(ex_project_not_found.format(old))
    if os.path.exists(os.path.join(projects_root, new)):
        raise NameAlreadyTaken(ex_project_exists.format(new))
    os.rename(os.path.join(projects_root, old), os.path.join(projects_root, new))
    complete_add(project=new)
    complete_remove(project=old)


def edit_project(name):
    """edits project start&stop files"""
    projects_root = get_projects_root()
    if name in print_list():
        edit_file(os.path.join(projects_root, name, "start.sh"))
        edit_file(os.path.join(projects_root, name, "stop.sh"))
    else:
        raise NameNotFound(ex_project_not_found.format(name))


def stop():
    """stops project"""
    os.kill(os.getppid(), signal.SIGKILL)


@lockable(check_only=True)
def remove_project(project):
    """removes project"""
    project_root = os.path.join(get_projects_root(), project)
    if os.path.exists(project_root):
        if not os.path.exists(os.path.join(project_root, "_lock")):
            if os.path.islink(project_root):
                os.remove(project_root)
            else:
                shutil.rmtree(project_root)
            complete_remove(project)
        else:
            raise ProjectActivated(ex_project_is_active.format(project))
    else:
        raise NameNotFound(ex_project_not_found.format(project))


@lockable(check_only=True)
def archive(project):
    """removes project"""
    project_root = os.path.join(get_projects_root(), project)
    if not os.path.exists(project_root):
        raise NameNotFound(ex_project_not_found.format(project))

    if not os.path.exists(os.path.join(project_root, "_lock")):
        raise ProjectActivated(ex_project_is_active.format(project))

    if project in print_old():
        raise NameAlreadyTaken(ex_project_in_archive.format(project))

    archive_root = get_archive_root()
    shutil.move(project_root, os.path.join(archive_root, project))
    complete_remove(project)


def restore(name):
    """restores project from archive"""
    if os.path.exists(os.path.join(get_archive_root(), name)):
        if name not in print_list():
            shutil.move(os.path.join(get_archive_root(), name), os.path.join(get_projects_root(), name))
            complete_add(name)
        else:
            raise NameAlreadyTaken(ex_project_exists.format(name))
    else:
        raise NameNotFound("{0} - project not found in {1} folder".format(name, get_archive_root()))


def clean():
    """unlocks all projects"""
    projects_root = get_projects_root()
    for dirname in os.listdir(projects_root):
        if os.path.exists(os.path.join(projects_root, dirname, "_lock")):
            os.remove(os.path.join(projects_root, dirname, "_lock"))


def print_project_for_root(projects_root):
    projects = [
        project
        for project in os.listdir(projects_root)
        if os.path.isdir(os.path.join(projects_root, project))
    ]
    return "\n".join(projects)


def print_list():
    """lists all projects"""
    projects_root = get_projects_root()
    return print_project_for_root(projects_root)


def print_old():
    """lists archived projects"""
    archive_root = get_archive_root()
    return print_project_for_root(archive_root)


def print_tasks(name):
    """lists tasks in project"""
    projects_root = get_projects_root()
    tasks = [
        # TODO: refactor V use filename
        task[:-3]
        for task in os.listdir(os.path.join(projects_root, name, "tasks"))
    ]
    return "\n".join(tasks)


def create_task(project, name):
    """creates task"""
    if not project_exist(project):
        raise NameNotFound(ex_project_not_found.format(project))

    if not task_exist(project, name):
        raise NameAlreadyTaken(ex_task_already_exists.format(name))

    project_root = os.path.join(get_projects_root(), project)
    Popen(["/bin/sh", "-c", "echo '#!/bin/sh' > {0}".format(os.path.join(project_root, "tasks",
                                                                         name + ".sh"))]).communicate(input)
    edit_file(os.path.join(project_root, "tasks", name + ".sh"))
    os.chmod(os.path.join(project_root, "tasks", name + ".sh"), 0o755)
    with open(os.path.join(project_root, "tasks.py"), mode='a') as tasks_file:
        tasks_file.write(new_task.format(name, project, name))
    with open(os.path.join(project_root, "tasks.sh"), mode='a') as tasks_alias_file:
        tasks_alias_file.write("alias {0}=\"pet {0}\"\n".format(name))
    print("alias available during next boot of project")


def edit_task(project, task):
    """edits task"""
    if task_exist(project, task):
        edit_file(os.path.join(get_projects_root(), project, "tasks", task + ".sh"))
    else:
        raise NameNotFound(ex_task_not_found.format(task))


def rename_task(project, old, new):
    """renames task"""
    project_tasks = os.path.join(get_projects_root(), project, "tasks")
    if not os.path.isfile(os.path.join(project_tasks, old + ".sh")):
        raise NameNotFound(ex_task_not_found.format(old))
    if os.path.isfile(os.path.join(project_tasks, new + ".sh")):
        raise NameAlreadyTaken(ex_task_already_exists.format(new))
    os.rename(os.path.join(project_tasks, old + ".sh"), os.path.join(project_tasks, new + ".sh"))


# TODO: refactor V s/active/active_project_name/
# TODO: refactor V s/project/project_name/
def run_task(project, task, active, interactive, args=()):
    """executes task in correct project"""
    if not task_exist(project, task):
        raise NameNotFound(ex_task_not_found.format(task))

    popen_args = [os.path.join(get_projects_root(), project, "tasks", task + ".sh")]
    popen_args.extend(list(args))
    if not os.path.isfile(os.path.join(PET_INSTALL_FOLDER, shell_profiles)):
        create_shell()
    if active == project:
        Popen(popen_args)
    else:
        if os.path.isfile(os.path.join(get_projects_root(), project, "_lock")):
            raise ProjectActivated(ex_project_is_active.format(project))
        project_root = os.path.join(get_projects_root(), project)
        if not os.path.exists(os.path.join(project_root, bashrc)) and \
                not os.path.exists(os.path.join(project_root, zshrc)):
            make_rc_file(project, project_root, os.environ.get('SHELL', ""))
        with ProjectLock(name=project):
            rc_type = get_rc_type(project_root)
            if rc_type:
                # TODO: refactor V change it to normal class
                with TaskExec(project, task, rc_type, interactive, list(args)):
                    pass


def remove_task(project, task):
    """removes task"""
    if not task_exist(project, task):
        raise NameNotFound("{0}/{1} - task not found in this project".format(project, task))

    project_root = os.path.join(get_projects_root(), project)
    num = Popen(["/bin/sh", "-c", "grep -n \"def {0}\" {1} | cut -d \":\" -f 1".format(
        task, os.path.join(project_root, "tasks.py"))], stdout=PIPE).stdout.read()
    num = int(num.decode("utf-8")[:-1])
    Popen(["/bin/sh", "-c", "sed -i -e \"{0},{1}d\" {2}".format(
        str(num-6), str(num+1), os.path.join(project_root, "tasks.py"))])
    Popen(["/bin/sh", "-c", "sed -i \"/alias {0}/d\" {1}".format(task, os.path.join(project_root, "tasks.sh"))])
    os.remove(os.path.join(project_root, "tasks", task + ".sh"))
