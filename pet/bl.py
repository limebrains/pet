# Python
import functools
import glob
import shutil
import signal
import os

from subprocess import (
    PIPE,
    Popen,
)

# Third party

# Own
from file_templates import (
    new_project_py_file_template,
    new_task_for_tasks_sh_template,
    new_tasks_sh_file_template,
)
from pet_exceptions import (
    NameAlreadyTaken,
    NameNotFound,
    PetException,
    ProjectActivated,
)


# TODO: you can remove/ archive active project out of other tab
# TODO: templates: tasks


PET_INSTALL_FOLDER = os.path.dirname(os.path.realpath(__file__))
PET_FOLDER = os.environ.get('PET_FOLDER', os.path.join(os.path.expanduser("~"), ".pet/"))
COMMANDS = "pet archive clean edit init list register remove rename restore stop task run".split()
BASH_RC_FILENAME = "bashrc"
ZSH_RC_FILENAME = ".zshrc"
SHELL_PROFILES_FILENAME = "shell_profiles"
EX_PROJECT_NOT_FOUND = "{0} - project not found"
EX_PROJECT_IS_ACTIVE = "{0} - project is active"
EX_PROJECT_EXISTS = "{0} - name already taken"
EX_PROJECT_IN_ARCHIVE = "{0} - name already taken in archive"
EX_TEMPLATE_NOT_FOUND = "{0} - template not found"
EX_TASK_NOT_FOUND = "{0} - task not found"
EX_TASK_ALREADY_EXISTS = "{0}- task already exists"
EX_SHELL_NOT_SUPPORTED = "{0} - isn't supported"
EX_NO_RC_FILE_FOUND = "no rc file in {0}"


def get_file_fullname(searching_root, file_name):
    return glob.glob(os.path.join(searching_root, file_name + '.*'))[0]


def get_file_fullname_and_path(searching_root, file_name):
    return os.path.join(searching_root, glob.glob(os.path.join(searching_root, file_name + '.*'))[0])


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


def edit_file(path):
    """edits file using $EDITOR"""
    Popen(["/bin/sh", "-c", "$EDITOR {0}".format(path)]).communicate(input)


def project_exist(project_name):
    """checks existence of project"""
    return os.path.exists(os.path.join(get_projects_root(), project_name))


def template_exist(template_name):
    """checks existence of project"""
    return os.path.exists(os.path.join(get_templates_root(), template_name))


def task_exist(project_name, task_name):
    """checks existence of task"""
    if '.' in task_name:
        task_name = os.path.splitext(task_name)[0]
    return task_name in print_tasks(project_name)


def complete_add(project_name):
    Popen(["/bin/sh", "-c", "sed -i '/projects=/ s/\"$/ {0}\"/' {1}".format(project_name, os.path.join(
        PET_INSTALL_FOLDER, "complete.bash"))])


def complete_remove(project_name):
    line_nr = Popen(["/bin/sh", "-c", "grep -n \"projects=\" {0} | cut -d \":\" -f 1".format(
        os.path.join(PET_INSTALL_FOLDER, "complete.bash"))],
                    stdout=PIPE).stdout.read()
    if line_nr:
        line_nr = int(line_nr.decode("utf-8")[:-1])
        Popen(["/bin/sh", "-c", "sed -i '{0}s/{1}//' {2}".format(
            line_nr, " " + project_name, os.path.join(PET_INSTALL_FOLDER, "complete.bash"))])


def lockable(check_only=True):
    def _lockable(func, *args, **kwargs):
        def __lockable(self=None, project_name='', *args, **kwargs):
            lock = kwargs.pop('lock', None)
            if os.path.isfile(os.path.join(get_projects_root(), project_name, "_lock")):
                raise ProjectActivated(EX_PROJECT_IS_ACTIVE.format(project_name))
            if not check_only or lock:
                with ProjectLock(project_name):
                    if self:
                        return func(self, project_name, *args, **kwargs)
                    else:
                        return func(project_name, *args, **kwargs)
            else:
                if self:
                    return func(self, project_name, *args, **kwargs)
                else:
                    return func(project_name, *args, **kwargs)
        return __lockable
    return _lockable


class GeneralShellMixin(object):

    def __init__(self):
        self.rc_filename = ""

    def get_rc_filename(self):
        return self.rc_filename

    def make_rc_file(self, project_name):
        project_root = os.path.join(get_projects_root(), project_name)
        contents = "source {0}/shell_profiles\nexport PET_ACTIVE_PROJECT='{1}'\nsource {2}/start.sh\n" \
                   "PS1=\"[{1}] $PS1\"\nsource {3}\n".format(PET_INSTALL_FOLDER, project_name, project_root,
                                                             os.path.join(project_root, "tasks.sh"))
        rc = os.path.join(project_root, self.get_rc_filename())
        with open(rc, mode='w') as rc_file:
            rc_file.write(contents)

    def start(self, project_root):
        pass

    def create_shell_profiles(self):
        pass

    def task_exec(self, project_name, task_name, interactive, args=()):
        tasks_root = os.path.join(get_projects_root(), project_name, "tasks")
        popen_args = [os.path.join(tasks_root, get_file_fullname(tasks_root, task_name))]
        popen_args.extend(args)
        Popen(popen_args)


class Bash(GeneralShellMixin):

    def __init__(self):
        GeneralShellMixin.__init__(self)
        self.rc_filename = BASH_RC_FILENAME

    def start(self, project_root):
        Popen(["/bin/sh", "-c", "$SHELL --rcfile {0}\n$SHELL {1}/stop.sh".format(
            os.path.join(project_root, self.get_rc_filename()), project_root)]).communicate(input)

    def create_shell_profiles(self):
        with open(os.path.join(PET_INSTALL_FOLDER, 'shell_profiles'), mode='w') as shell_profiles_file:
            if os.path.isfile(os.path.join(os.path.expanduser("~"), '.bashrc')):
                shell_profiles_file.write("source ~/.bashrc\n")
            if os.path.isfile(os.path.join(os.path.expanduser("~"), '.profile')):
                shell_profiles_file.write("source ~/.profile\n")
            if os.path.isfile(os.path.join(os.path.expanduser("~"), '.bash_profile')):
                shell_profiles_file.write("source ~/.bash_profile\n")

    @lockable()
    def task_exec(self, project_name, task_name, interactive, args=()):
        if interactive:
            self.make_rc_file(project_name)
            project_root = os.path.join(get_projects_root(), project_name)
            # TODO: change /bin/bash for usr bin env bash, maybe with Popen -> which usrbin bash -> cut
            Popen(["/bin/bash", "-c", "$SHELL --rcfile <(echo '. {0}; {1} {2}')\n$SHELL {3}/stop.sh".format(
                os.path.join(project_root, self.get_rc_filename()),
                get_file_fullname_and_path(os.path.join(project_root, "tasks"), task_name),
                " ".join(args),
                project_root)]).communicate(input)
        else:
            GeneralShellMixin.task_exec(self, project_name, task_name, interactive, args)


class Zsh(GeneralShellMixin):

    def __init__(self):
        GeneralShellMixin.__init__(self)
        self.rc_filename = ZSH_RC_FILENAME

    def start(self, project_root):
        print('I am doing (actually not - I forgot about it - but it is a print so may be someday i will do it)')
        Popen(["/bin/sh", "-c", "ZDOTDIR={0} $SHELL\n$SHELL {0}/stop.sh".format(
            project_root)]).communicate(input)

    def create_shell_profiles(self):
        if os.environ.get('ZDOTDIR', ""):
            with open(os.path.join(PET_INSTALL_FOLDER, 'shell_profiles'), mode='w') as shell_profiles_file:
                shell_profiles_file.write("source $ZDOTDIR/.zshrc\n")
        else:
            with open(os.path.join(PET_INSTALL_FOLDER, 'shell_profiles'), mode='w') as shell_profiles_file:
                shell_profiles_file.write("source $HOME/.zshrc\n")

    @lockable()
    def task_exec(self, project_name, task_name, interactive, args=()):
        if interactive:
            # TODO: find a way to make interactive tasks in zsh
            print("it doesn't work in zsh")
        else:
            GeneralShellMixin.task_exec(self, project_name, task_name, interactive, args)


@functools.lru_cache()
def get_shell():
    shell_name = os.environ.get('SHELL', '')
    if 'bash' in shell_name:
        shell = Bash()
    elif 'zsh' in shell_name:
        shell = Zsh()
    else:
        raise NameNotFound(EX_SHELL_NOT_SUPPORTED.format(os.environ.get('SHELL', 'not found $SHELL')))
    return shell


class ProjectLock(object):

    def __init__(self, project_name):

        if not os.path.exists(os.path.join(get_projects_root(), project_name)):
            raise NameNotFound(EX_PROJECT_NOT_FOUND.format(project_name))
        self.filepath = os.path.join(get_projects_root(), project_name, "_lock")

    def __enter__(self):
        self.open_file = open(self.filepath, "w")

    def __exit__(self, *args):
        self.open_file.close()
        os.remove(self.filepath)


class ProjectCreator(object):

    def __init__(self, project_name, templates=()):
        self.projects_root = get_projects_root()
        self.templates_root = get_templates_root()
        self.project_name = project_name
        self.project_root = os.path.join(self.projects_root, self.project_name)
        self.templates = templates
        self.check_name()
        self.check_templates()

    def check_name(self):
        if self.project_name in print_list():
            raise NameAlreadyTaken(EX_PROJECT_EXISTS.format(self.project_name))
        if self.project_name in COMMANDS:
            raise NameAlreadyTaken("{0} - there is pet command with this name".format(self.project_name))

    def check_templates(self):
        for template in self.templates:
            if not template_exist(template):
                raise NameNotFound(EX_TEMPLATE_NOT_FOUND.format(template))

    def create_dirs(self):
        if not os.path.isfile(os.path.join(PET_INSTALL_FOLDER, SHELL_PROFILES_FILENAME)):
            get_shell().create_shell_profiles()
        if not os.path.exists(os.path.join(self.project_root, "tasks")):
            os.makedirs(os.path.join(self.project_root, "tasks"))
        get_shell().make_rc_file(self.project_name)

    def create_additional_files(self):
        with open(os.path.join(self.project_root, self.project_name + ".py"), mode='w') as project_file:
            project_file.write(new_project_py_file_template.format(self.project_name))
        with open(os.path.join(self.project_root, "tasks.py"), mode='w') as tasks_file:
            tasks_file.write(new_tasks_sh_file_template)
        with open(os.path.join(self.project_root, "tasks.sh"), mode='w') as tasks_alias_file:
            tasks_alias_file.write("# aliases for your tasks\n")

    def create_file_with_templates(self, filename):
        with open(os.path.join(self.project_root, filename), mode='w') as file:
            if self.templates:
                file.write("# TEMPLATES\n")
                for template in self.templates:
                    file.write("# from template: {0}\n".format(template))
                    with open(os.path.join(self.templates_root, template, filename)) as corresponding_template_file:
                        file.write(corresponding_template_file.read())
                    file.write("\n")
                file.write("# check if correctly imported templates\n")
            else:
                file.write('# add here shell code to be executed while entering project\n')

    def create_start(self):
        self.create_file_with_templates("start.sh")

    def create_stop(self):
        self.create_file_with_templates("stop.sh")

    def edit(self):
        edit_file(os.path.join(self.project_root, "start.sh"))
        edit_file(os.path.join(self.project_root, "stop.sh"))

    def create(self):
        self.create_dirs()
        self.create_additional_files()
        self.create_start()
        self.create_stop()
        self.edit()
        complete_add(self.project_name)


@lockable()
def start(project_name):
    """starts new project"""
    if not os.path.isfile(os.path.join(PET_INSTALL_FOLDER, SHELL_PROFILES_FILENAME)):
        get_shell().create_shell_profiles()
    project_root = os.path.join(get_projects_root(), project_name)
    get_shell().make_rc_file(project_name)
    get_shell().start(project_root)


def create(project_name, templates=()):
    """creates new project"""
    ProjectCreator(project_name, templates).create()


def register():
    """adds symbolic link to .pet folder in projects"""
    folder = os.getcwd()
    project_name = os.path.basename(folder)
    if project_exist(project_name):
        raise NameAlreadyTaken(EX_PROJECT_EXISTS.format(project_name))

    if not (os.path.isfile(os.path.join(folder, project_name + ".py")) and
            os.path.isfile(os.path.join(folder, "start.sh")) and
            os.path.isfile(os.path.join(folder, "stop.sh")) and
            os.path.isfile(os.path.join(folder, "tasks.py")) and
            os.path.isdir(os.path.join(folder, "tasks"))):
        raise PetException("Haven't found all 5 files and tasks folder in\n{0}".format(folder))

    os.symlink(folder, os.path.join(get_projects_root(), project_name))
    complete_add(project_name)


def rename_project(old_project_name, new_project_name):
    """renames projects"""
    projects_root = get_projects_root()
    if not os.path.exists(os.path.join(projects_root, old_project_name)):
        raise NameNotFound(EX_PROJECT_NOT_FOUND.format(old_project_name))
    if os.path.exists(os.path.join(projects_root, new_project_name)):
        raise NameAlreadyTaken(EX_PROJECT_EXISTS.format(new_project_name))
    os.rename(os.path.join(projects_root, old_project_name), os.path.join(projects_root, new_project_name))
    complete_add(new_project_name)
    complete_remove(old_project_name)


def edit_project(project_name):
    """edits project start&stop files"""
    projects_root = get_projects_root()
    if project_name not in print_list():
        raise NameNotFound(EX_PROJECT_NOT_FOUND.format(project_name))

    edit_file(os.path.join(projects_root, project_name, "start.sh"))
    edit_file(os.path.join(projects_root, project_name, "stop.sh"))


def stop():
    """stops project"""
    os.kill(os.getppid(), signal.SIGKILL)


@lockable()
def remove_project(project_name):
    """removes project"""
    project_root = os.path.join(get_projects_root(), project_name)
    if not os.path.exists(project_root):
        raise NameNotFound(EX_PROJECT_NOT_FOUND.format(project_name))

    if os.path.islink(project_root):
        os.remove(project_root)
    else:
        shutil.rmtree(project_root)
    complete_remove(project_name)


@lockable()
def archive(project_name):
    """removes project"""
    project_root = os.path.join(get_projects_root(), project_name)
    if not os.path.exists(project_root):
        raise NameNotFound(EX_PROJECT_NOT_FOUND.format(project_name))
    if project_name in print_old():
        raise NameAlreadyTaken(EX_PROJECT_IN_ARCHIVE.format(project_name))

    archive_root = get_archive_root()
    shutil.move(project_root, os.path.join(archive_root, project_name))
    complete_remove(project_name)


def restore(project_name):
    """restores project from archive"""
    if not os.path.exists(os.path.join(get_archive_root(), project_name)):
        raise NameNotFound("{0} - project not found in {1} folder".format(project_name, get_archive_root()))
    if project_name in print_list():
        raise NameAlreadyTaken(EX_PROJECT_EXISTS.format(project_name))

    shutil.move(os.path.join(get_archive_root(), project_name), os.path.join(get_projects_root(), project_name))
    complete_add(project_name)


def clean():
    """unlocks all projects"""
    projects_root = get_projects_root()
    for dirname in os.listdir(projects_root):
        if os.path.exists(os.path.join(projects_root, dirname, "_lock")):
            os.remove(os.path.join(projects_root, dirname, "_lock"))


def print_projects_for_root(projects_root):
    projects = [
        project
        for project in os.listdir(projects_root)
        if os.path.isdir(os.path.join(projects_root, project))
        ]
    return "\n".join(projects)


def print_list():
    """lists all projects"""
    return print_projects_for_root(get_projects_root())


def print_old():
    """lists archived projects"""
    return print_projects_for_root(get_archive_root())


def print_tasks(project_name):
    """lists tasks in project"""
    projects_tasks_root = os.path.join(get_projects_root(), project_name, "tasks")
    tasks = [os.path.splitext(task)[0]
             for task in os.listdir(projects_tasks_root)]
    return "\n".join(tasks)


def create_task(project_name, task_name):
    """creates task"""
    if not project_exist(project_name):
        raise NameNotFound(EX_PROJECT_NOT_FOUND.format(project_name))
    if task_exist(project_name, task_name):
        raise NameAlreadyTaken(EX_TASK_ALREADY_EXISTS.format(task_name))

    project_root = os.path.join(get_projects_root(), project_name)
    if '.' in task_name:
        task_file_path = os.path.join(project_root, "tasks", task_name)
        task_name = os.path.splitext(task_name)[0]
        Popen(["/bin/sh", "-c", "echo 'add shebang to make sure file will be executable' > {0}".format(task_file_path)])
    else:
        task_file_path = os.path.join(project_root, "tasks", task_name + ".sh")
        Popen(["/bin/sh", "-c", "echo '#!/bin/sh' > {0}".format(task_file_path)])
    edit_file(task_file_path)
    os.chmod(task_file_path, 0o755)
    with open(os.path.join(project_root, "tasks.py"), mode='a') as tasks_file:
        tasks_file.write(new_task_for_tasks_sh_template.format(task_name, project_name, task_name))
    with open(os.path.join(project_root, "tasks.sh"), mode='a') as tasks_alias_file:
        tasks_alias_file.write("alias {0}=\"pet {0}\"\n".format(task_name))
    raise PetException("alias available during next boot of project")


def edit_task(project_name, task_name):
    """edits task"""
    if not task_exist(project_name, task_name):
        raise NameNotFound(EX_TASK_NOT_FOUND.format(task_name))

    edit_file(get_file_fullname_and_path(os.path.join(get_projects_root(), project_name, "tasks"), task_name))


def rename_task(project_name, old_task_name, new_task_name):
    """renames task"""
    tasks_root = os.path.join(get_projects_root(), project_name, "tasks")
    if not task_exist(project_name, old_task_name):
        raise NameNotFound(EX_TASK_NOT_FOUND.format(old_task_name))
    if task_exist(project_name, new_task_name):
        raise NameAlreadyTaken(EX_TASK_ALREADY_EXISTS.format(new_task_name))

    old_task_full_path = get_file_fullname_and_path(tasks_root, old_task_name)
    task_extension = os.path.splitext(old_task_full_path)[1]
    os.rename(old_task_full_path, os.path.join(tasks_root, new_task_name + task_extension))


def run_task(project_name, task_name, interactive, args=()):
    """executes task in correct project"""
    if not task_exist(project_name, task_name):
        raise NameNotFound(EX_TASK_NOT_FOUND.format(task_name))
    if not os.path.isfile(os.path.join(PET_INSTALL_FOLDER, SHELL_PROFILES_FILENAME)):
        get_shell().create_shell_profiles()
    get_shell().task_exec(project_name, task_name, interactive, args)


def remove_task(project_name, task_name):
    """removes task"""
    if not task_exist(project_name, task_name):
        raise NameNotFound("{0}/{1} - task not found in this project".format(project_name, task_name))

    project_root = os.path.join(get_projects_root(), project_name)
    num = Popen(["/bin/sh", "-c", "grep -n \"def {0}\" {1} | cut -d \":\" -f 1".format(
        task_name, os.path.join(project_root, "tasks.py"))], stdout=PIPE).stdout.read()
    num = int(num.decode("utf-8")[:-1])
    Popen(["/bin/sh", "-c", "sed -i -e \"{0},{1}d\" {2}".format(
        str(num-6), str(num+1), os.path.join(project_root, "tasks.py"))])
    Popen(["/bin/sh", "-c", "sed -i \"/alias {0}/d\" {1}".format(task_name, os.path.join(project_root, "tasks.sh"))])
    os.remove(get_file_fullname_and_path(os.path.join(project_root, "tasks"), task_name))