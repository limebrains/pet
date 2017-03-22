from subprocess import Popen, PIPE
import os
import signal
import shutil
from pet_exceptions import NameAlreadyTaken, NameNotFound, ProjectActivated
from file_templates import new_tasks_file, new_project_py_file, new_task

# TODO: sort functions
# TODO: make tasks not only in .sh
# TODO: get rid of hardcoded names like "tmp_bashrc", "PET_FOLDER", "projects", etc.


PET_INSTALL_FOLDER = os.path.dirname(os.path.realpath(__file__))
PET_FOLDER = os.environ.get('PET_FOLDER', os.path.join(os.path.expanduser("~"), ".pet/"))
commands = ("pet", "archive", "clean", "edit", "init", "list", "register", "remove", "rename", "restore", "stop", "task", "run")


def get_pet_install_folder():
    return PET_INSTALL_FOLDER


def get_pet_folder():
    return PET_FOLDER


def get_projects_root():
    if os.path.exists(os.path.join(PET_FOLDER, "projects")):
        return os.path.join(PET_FOLDER, "projects")


def get_archive_root():
    if os.path.exists(os.path.join(PET_FOLDER, "old")):
        return os.path.join(PET_FOLDER, "old")


def get_shell_as_type():
    if os.environ.get('SHELL', "").find('bash') != -1:
        return "tmp_bashrc"
    elif os.environ.get('SHELL', "").find('zsh') != -1:
        return ".zshrc"


def get_rc_file(project_root):
    if os.path.isfile(os.path.join(project_root, "tmp_bashrc")):
        return os.path.join(project_root, "tmp_bashrc")
    elif os.path.isfile(os.path.join(project_root, ".zshrc")):
        return os.path.join(project_root, ".zshrc")


def get_rc_type(project_root):
    if os.environ.get('SHELL', "").find('bash') != -1 and os.path.isfile(os.path.join(project_root, "tmp_bashrc")):
        return "tmp_bashrc"
    elif os.environ.get('SHELL', "").find('zsh') != -1 and os.path.isfile(os.path.join(project_root, ".zshrc")):
        return ".zshrc"


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
                run_path = os.path.join(self.project_root, 'run.bash')
                with open(run_path, mode='w') as run:
                    run.write("#!/usr/bin/env bash\n$SHELL --rcfile <(echo '. {0}; {1}')\n".format(
                        os.path.join(self.project_root, "tmp_bashrc"),
                        os.path.join(self.project_root, "tasks", self.task + ".sh")))
                os.chmod(run_path, 0o755)
                Popen(["/bin/sh", "-c", "{0}\n$SHELL {1}/stop.sh".format(
                    run_path, self.project_root)]).communicate(input)
                os.remove(run_path)
            elif self.shell.find('zsh') != -1:
                # TODO: here it DOESN't work
                print("it doesn't work in zsh")
                Popen(["/bin/sh", "-c", "ZDOTDIR={0} $SHELL\n$SHELL {0}/stop.sh".format(
                    self.project_root)]).communicate(input)
            else:
                raise NameNotFound("{0} - isn't supported".format(self.shell))
        else:
            popen_args = [os.path.join(self.project_root, "tasks", self.task + ".sh")]
            popen_args.extend(self.args)
            Popen(popen_args)

    def __exit__(self, *args):
        pass


def create_shell():
    shell = os.environ.get('SHELL', "")
    if shell.find('bash') != -1:
        with open(os.path.join(PET_INSTALL_FOLDER, 'shell_profiles'), mode='w') as shell_profiles:
            if os.path.isfile(os.path.join(os.path.expanduser("~"), '.bashrc')):
                shell_profiles.write("source ~/.bashrc\n")
            if os.path.isfile(os.path.join(os.path.expanduser("~"), '.profile')):
                shell_profiles.write("source ~/.profile\n")
            if os.path.isfile(os.path.join(os.path.expanduser("~"), '.bash_profile')):
                shell_profiles.write("source ~/.bash_profile\n")
    elif shell.find('zsh') != -1:
        if os.environ.get('ZDOTDIR', ""):
            with open(os.path.join(PET_INSTALL_FOLDER, 'shell_profiles'), mode='w') as shell_profiles:
                shell_profiles.write("source $ZDOTDIR/.zshrc\n")
        else:
            with open(os.path.join(PET_INSTALL_FOLDER, 'shell_profiles'), mode='w') as shell_profiles:
                shell_profiles.write("source $HOME/.zshrc\n")
    else:
        raise NameNotFound("{0} - isn't supported".format(shell))


class ProjectCreator(object):

    def __init__(self, name, templates=()):
        self.projects_root = get_projects_root()
        self.name = name
        self.project_root = os.path.join(self.projects_root, self.name)
        self.templates = templates
        self.check_name()
        self.check_templates()

    def check_name(self):
        if self.name in print_list():
            raise NameAlreadyTaken("{0} - name already taken".format(self.name))
        if self.name in commands:
            raise NameAlreadyTaken("{0} - there is pet command with this name".format(self.name))

    def check_templates(self):
        for template in self.templates:
            if not project_exist(template):
                raise NameNotFound("{0} - template not found".format(template))

    def create_dirs(self):
        if not os.path.isfile(os.path.join(PET_INSTALL_FOLDER, "shell_profiles")):
            create_shell()
        if not os.path.exists(self.project_root):
            os.makedirs(self.project_root)
        if not os.path.exists(os.path.join(self.project_root, "tasks")):
            os.makedirs(os.path.join(self.project_root, "tasks"))
        make_rc_file(self.name, self.project_root, os.environ.get('SHELL', ""))

    def create_additional_files(self):
        with open(os.path.join(self.project_root, self.name + ".py"), mode='w') as project_file:
            project_file.write(new_project_py_file.format(self.name))
        with open(os.path.join(self.project_root, "tasks.py"), mode='w') as tasks_file:
            tasks_file.write(new_tasks_file)
        with open(os.path.join(self.project_root, "tasks.sh"), mode='w') as tasks_alias_file:
            tasks_alias_file.write("# aliases for your tasks\n")

    def create_start(self):
        with open(os.path.join(self.project_root, "start.sh"), mode='w') as start_file:
            if self.templates:
                start_file.write("# TEMPLATES\n")
                for template in self.templates:
                    start_file.write("# from template: {0}\n".format(template))
                    template_start_file = open(os.path.join(self.projects_root, template, "start.sh"))
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
                    template_stop_file = open(os.path.join(self.projects_root, template, "stop.sh"))
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


def edit_file(path):
    """edits file using $EDITOR"""
    Popen(["/bin/sh", "-c", "$EDITOR {0}".format(path)]).communicate(input)


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


def start(name):
    """starts new project"""
    if not os.path.isfile(os.path.join(PET_INSTALL_FOLDER, "shell_profiles")):
        create_shell()
    with ProjectLock(name):
        project_root = os.path.join(get_projects_root(), name)
        shell = os.environ.get('SHELL', "")
        make_rc_file(name, project_root, shell)
        if shell.find('bash') != -1:
            Popen(["/bin/sh", "-c", "$SHELL --rcfile {0}\n$SHELL {1}/stop.sh".format(
                os.path.join(project_root, 'tmp_bashrc'), project_root)]).communicate(input)
        elif shell.find('zsh') != -1:
            print('I am doing this!')
            Popen(["/bin/sh", "-c", "ZDOTDIR={0} $SHELL\n$SHELL {0}/stop.sh".format(
                project_root)]).communicate(input)
        else:
            raise NameNotFound("{0} - isn't supported".format(shell))


def project_exist(name):
    """checks existence of project"""
    return os.path.exists(os.path.join(get_projects_root(), name))


def task_exist(project, name):
    """checks existence of task"""
    return os.path.exists(os.path.join(get_projects_root(), project, "tasks", name + ".sh"))


def stop():
    """stops project"""
    os.kill(os.getppid(), signal.SIGKILL)


def create(name, templates=()):
    """creates new project"""
    ProjectCreator(name, templates).create()


def create_task(project, name):
    """creates task"""
    if project_exist(project):
        if not task_exist(project, name):
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


def print_old():
    """lists archived projects"""
    projects_root = get_archive_root()
    projects = [
        project
        for project in os.listdir(projects_root[0])
        if os.path.isdir(os.path.join(projects_root[0], project))
    ]
    if projects:
        return "\n".join(projects)


def print_tasks(name):
    """lists tasks in project"""
    projects_root = get_projects_root()
    tasks = [
        task[:-3]
        for task in os.listdir(os.path.join(projects_root, name, "tasks"))
    ]
    if tasks:
        return "\n".join(tasks)


def remove_project(project):
    """removes project"""
    project_root = os.path.join(get_projects_root(), project)
    if os.path.exists(project_root):
        if not os.path.exists(os.path.join(project_root, "_lock")):
            if os.path.islink(project_root):
                os.remove(project_root)
            else:
                shutil.rmtree(project_root)
        else:
            raise ProjectActivated("{0} - project is active".format(project))
    else:
        raise NameNotFound("{0} - project not found".format(project))


def archive(project):
    """removes project"""
    project_root = os.path.join(get_projects_root(), project)
    if os.path.exists(project_root):
        if not os.path.exists(os.path.join(project_root, "_lock")):
            archive_root = get_archive_root()[0]
            shutil.move(project_root, os.path.join(archive_root, project))
        else:
            raise ProjectActivated("{0} - project is active".format(project))
    else:
        raise NameNotFound("{0} - project not found".format(project))


def remove_task(project, task):
    """removes task"""
    if task_exist(project, task):
        project_root = os.path.join(get_projects_root(), project)
        num = Popen(["/bin/sh", "-c", "grep -n \"def {0}\" {1} | cut -d \":\" -f 1".format(
            task, os.path.join(project_root, "tasks.py"))], stdout=PIPE).stdout.read()
        num = int(num.decode("utf-8")[:-1])
        Popen(["/bin/sh", "-c", "sed -i -e \"{0},{1}d\" {2}".format(
            str(num-6), str(num+1), os.path.join(project_root, "tasks.py"))])
        Popen(["/bin/sh", "-c", "sed -i \"/alias {0}/d\" {1}".format(task, os.path.join(project_root, "tasks.sh"))])
        os.remove(os.path.join(project_root, "tasks", task + ".sh"))
    else:
        raise NameNotFound("{0}/{1} - task not found in this project".format(project, task))


def restore(name):
    """restores project from archive"""
    if os.path.exists(os.path.join(get_archive_root(), name)):
        shutil.move(os.path.join(get_archive_root(), name), os.path.join(get_projects_root(), name))
    else:
        raise NameNotFound("{0} - project not found in \"old\" folder".format(name))


def register():
    """adds symbolic link to .pet folder in projects"""
    folder = os.getcwd()
    name = os.path.basename(folder)
    if not project_exist(name):
        if (os.path.exists(os.path.join(folder, name + ".py")) and
                os.path.exists(os.path.join(folder, "start.sh")) and
                os.path.exists(os.path.join(folder, "stop.sh")) and
                os.path.exists(os.path.join(folder, "tasks.py")) and
                os.path.exists(os.path.join(folder, "tasks"))):
            os.symlink(folder, os.path.join(get_projects_root(), name))
        else:
            return "Haven't found all 5 files and tasks folder in\n{0}".format(folder)
    else:
        raise NameAlreadyTaken("{0} - name already taken".format(name))


def clean():
    """unlocks all projects"""
    projects_root = get_projects_root()
    for dirname in os.listdir(projects_root):
        if os.path.exists(os.path.join(projects_root, dirname, "_lock")):
            os.remove(os.path.join(projects_root, dirname, "_lock"))


def rename_project(old, new):
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


def run_task(project, task, active, interactive, args=()):
    """executes task in correct project"""
    if task_exist(project, task):
        popen_args = [os.path.join(get_projects_root(), project, "tasks", task + ".sh")]
        popen_args.extend(list(args))
        if not os.path.isfile(os.path.join(PET_INSTALL_FOLDER, "shell_profiles")):
            create_shell()
        if active == project:
            Popen(popen_args)
        else:
            if os.path.isfile(os.path.join(get_projects_root(), project, "_lock")):
                raise ProjectActivated("{0} - project already activated".format(project))
            project_root = os.path.join(get_projects_root(), project)
            if not os.path.exists(os.path.join(project_root, "tmp_bashrc")) and \
                    not os.path.exists(os.path.join(project_root, ".zshrc")):
                make_rc_file(project, project_root, os.environ.get('SHELL', ""))
            with ProjectLock(name=project):
                rc_type = get_rc_type(project_root)
                if rc_type:
                    with TaskExec(project, task, rc_type, interactive, list(args)):
                        pass
                else:
                    pass
    else:
        raise NameNotFound("{0} - task not found".format(task))


def edit_task(project, task):
    """edits task"""
    if task_exist(project, task):
        edit_file(os.path.join(get_projects_root(), project, "tasks", task + ".sh"))
    else:
        raise NameNotFound("{0} - task not found".format(task))


def rename_task(project, old, new):
    """renames task"""
    project_tasks = os.path.join(get_projects_root(), project, "tasks")
    if not os.path.isfile(os.path.join(project_tasks, old + ".sh")):
        raise NameNotFound("{0}/{1} - task not found".format(project, old))
    if os.path.isfile(os.path.join(project_tasks, new + ".sh")):
        raise NameAlreadyTaken("{0}/{1} - new name already taken".format(project, new))
    os.rename(os.path.join(project_tasks, old + ".sh"), os.path.join(project_tasks, new + ".sh"))
