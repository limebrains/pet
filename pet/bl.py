try:
    from functools import lru_cache
except ImportError:
    from backports.functools_lru_cache import lru_cache
import glob
import logging
import os
import shutil
import signal
from subprocess import PIPE, Popen

from pet.exceptions import (
    ExceptionMessages,
    Info,
    NameAlreadyTaken,
    NameNotFound,
    PetException,
    ProjectActivated,
    ShellNotRecognized,
    FolderNotFound,
)
from pet.file_templates import (
    new_project_rc_template,
    new_start_sh_template,
)

from pet.utils import makedirs

log = logging.getLogger(__file__)

# TODO: REDO totally templates before release
# TODO: rewrite logging into yields
# TODO: what about histfiles?
# TODO: zsh known issues: no tasks for now; auto-completion works only for full words


COMMANDS = "pet archive edit init list register remove rename restore stop task run".split()
BASH_RC_FILENAME = "bashrc"
ZSH_RC_FILENAME = ".zshrc"
BASH_PROFILES_FILENAME = "bash_profiles"
ZSH_PROFILES_FILENAME = "zsh_profiles"
# TODO: github:dmydlo also in install.bash
SETUP_FILE_FOR_VERSION = "https://raw.githubusercontent.com/dmydlo/pet/master/setup.py"


def get_file_fullname(searching_root, file_name):
    output = glob.glob(os.path.join(searching_root, file_name + '.*'))
    if output:
        return output[0]
    else:
        return glob.glob(os.path.join(searching_root, file_name))[0]


def get_file_fullname_and_path(searching_root, file_name):
    name = glob.glob(os.path.join(searching_root, file_name + '.*'))
    if name:
        return os.path.join(searching_root, name[0])
    else:
        return os.path.join(searching_root, glob.glob(os.path.join(searching_root, file_name))[0])


def get_pet_install_folder():
    directory = os.path.dirname(os.path.realpath(__file__))
    if os.path.exists(directory):
        return directory
    else:
        raise FolderNotFound(ExceptionMessages.directory_not_found.value.format(directory))


def get_pet_folder():
    directory = os.path.expanduser(os.environ.get('PET_FOLDER', "~/.pet/"))
    if os.path.exists(directory):
        return directory
    else:
        raise FolderNotFound(ExceptionMessages.directory_not_found.value.format(directory))


def get_projects_root():
    directory = os.path.join(get_pet_folder(), "projects")
    if os.path.exists(directory):
        return directory
    else:
        raise FolderNotFound(ExceptionMessages.directory_not_found.value.format(directory))


def get_projects_templates_root():
    directory = os.path.join(get_pet_folder(), "templates", "projects")
    if os.path.exists(directory):
        return directory
    else:
        raise FolderNotFound(ExceptionMessages.directory_not_found.value.format(directory))


def get_tasks_templates_root():
    directory = os.path.join(get_pet_folder(), "templates", "tasks")
    if os.path.exists(directory):
        return directory
    else:
        raise FolderNotFound(ExceptionMessages.directory_not_found.value.format(directory))


def get_archive_root():
    directory = os.path.join(get_pet_folder(), "archive")
    if os.path.exists(directory):
        return directory
    else:
        raise FolderNotFound(ExceptionMessages.directory_not_found.value.format(directory))


def edit_file(path):
    """edits file using EDITOR variable from config file"""
    Popen(["/bin/sh",
           "-c",
           """PET_EDITOR=$(grep '^EDITOR==' {0} | sed -n \"/EDITOR==/s/EDITOR==//p\")
            if [ -z "$PET_EDITOR" ]; then
                if [ -z "$EDITOR" ]; then
                    echo "haven't found either $EDITOR, either EDITOR in pet config - trying vi"
                    /usr/bin/vi {1}
                else
                    $EDITOR {1}
                fi
            else
                $PET_EDITOR {1}
            fi""".format(
                os.path.join(get_pet_folder(), "config"), path)]).communicate()


def project_exist(project_name):
    """checks existence of project"""
    return os.path.exists(os.path.join(get_projects_root(), project_name))


def project_template_exist(template_name):
    """checks existence of project"""
    return os.path.exists(os.path.join(get_projects_templates_root(), template_name))


def task_exist(project_name, task_name):
    """checks existence of task"""
    if '.' in task_name:
        task_name = os.path.splitext(task_name)[0]
    return task_name in print_tasks(project_name).split('\n')


def how_many_active(project_name):
    nums = Popen([
        "/bin/sh",
        "-c",
        "ps aux | grep \"#pet {0}=\" | sed -n \"s/.*#pet {0}=\([0-9][0-9]*\).*/\\1/p\"".format(
            project_name)
    ], stdout=PIPE
    ).stdout.read()
    nums = nums.splitlines()
    if nums:
        return max([int(num) for num in nums])
    else:
        return 0


def check_version():
    newest_version = Popen([
        "/bin/sh",
        "-c",
        "curl -fsSL {0} | grep 'version=' | sed -n \"s/.*='\(.*\)'.*/\\1/p\"".format(SETUP_FILE_FOR_VERSION),
    ], stdout=PIPE).stdout.read()
    return newest_version[:-1]


def recreate():
    print("Creating pet files in {0}".format(get_pet_folder()))
    makedirs(path=os.path.join(get_pet_folder(), "projects"), exists_ok=True)
    makedirs(path=os.path.join(get_pet_folder(), "archive"), exists_ok=True)
    makedirs(path=os.path.join(get_pet_folder(), "templates", "projects"), exists_ok=True)
    makedirs(path=os.path.join(get_pet_folder(), "templates", "tasks"), exists_ok=True)
    Popen(["/bin/sh", "-c", "echo \"EDITOR==$EDITOR\" > {0}".format(
        os.path.join(get_pet_folder(), "config"),
    )])


def lockable(check_only_projects=True, check_active=False):
    def _lockable(func, *args, **kwargs):
        def __lockable(self=None, project_name='', check_only=check_only_projects, *args, **kwargs):
            check_only = not kwargs.pop('lock', not check_only)
            if os.path.isfile(os.path.join(get_projects_root(), project_name, "_lock")):
                raise ProjectActivated(ExceptionMessages.project_is_locked.value.format(project_name))
            if check_active:
                if how_many_active(project_name):
                    raise ProjectActivated(ExceptionMessages.project_is_active.value.format(project_name))
            if not check_only:
                if how_many_active(project_name):
                    log.warning(ExceptionMessages.project_is_active.value.format(project_name))
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
        self.shell_profiles = ""

    def get_rc_filename(self):
        return self.rc_filename

    def get_shell_profiles(self):
        return self.shell_profiles

    def make_rc_file(self, project_name, nr, additional_lines=""):
        project_root = os.path.join(get_projects_root(), project_name)
        if nr == 1:
            nr = ""
        contents = new_project_rc_template.format(
            get_pet_folder(),
            project_name,
            project_root,
            os.path.join(project_root, "tasks.sh"),
            additional_lines,
            nr,
            self.get_shell_profiles(),
        )
        rc = os.path.join(project_root, self.get_rc_filename())
        with open(rc, mode='w') as rc_file:
            rc_file.write(contents)

    def start(self, project_root, project_name):
        raise ShellNotRecognized(
            ExceptionMessages.shell_not_supported.value.format(os.environ.get('SHELL', 'not found $SHELL')))

    def create_shell_profiles(self):
        raise ShellNotRecognized(
            ExceptionMessages.shell_not_supported.value.format(os.environ.get('SHELL', 'not found $SHELL')))

    def task_exec(self, project_name, task_name, interactive, args=()):
        raise ShellNotRecognized(
            ExceptionMessages.shell_not_supported.value.format(os.environ.get('SHELL', 'not found $SHELL')))

    def edit_shell_profiles(self):
        raise ShellNotRecognized(
            ExceptionMessages.shell_not_supported.value.format(os.environ.get('SHELL', 'not found $SHELL')))


class Bash(GeneralShellMixin):

    def __init__(self):
        GeneralShellMixin.__init__(self)
        self.rc_filename = BASH_RC_FILENAME
        self.shell_profiles = BASH_PROFILES_FILENAME

    def start(self, project_root, project_name):
        amount_active = how_many_active(project_name)
        self.make_rc_file(project_name, amount_active + 1, additional_lines="")
        Popen(["/bin/sh",
               "-c",
               "#pet {0}={1}\n$SHELL --rcfile {2}\nprintf ''".format(
                   project_name,
                   amount_active + 1,
                   os.path.join(project_root, self.get_rc_filename()),
               )
               ]).communicate()

    def create_shell_profiles(self):
        if not os.path.isfile(os.path.join(get_pet_folder(), BASH_PROFILES_FILENAME)):
            with open(os.path.join(get_pet_folder(), BASH_PROFILES_FILENAME), mode='w') as bash_profiles:
                if os.path.isfile(os.path.join(os.path.expanduser("~"), '.bashrc')):
                    bash_profiles.write("source ~/.bashrc\n")
                if os.path.isfile(os.path.join(os.path.expanduser("~"), '.profile')):
                    bash_profiles.write("source ~/.profile\n")
                if os.path.isfile(os.path.join(os.path.expanduser("~"), '.bash_profile')):
                    bash_profiles.write("source ~/.bash_profile\n")

    @lockable()
    def task_exec(self, project_name, task_name, interactive, args=()):
        amount_active = how_many_active(project_name)
        project_root = os.path.join(get_projects_root(), project_name)
        if interactive:
            self.make_rc_file(project_name, nr=0, additional_lines=". {0} {1}\n".format(
                get_file_fullname_and_path(os.path.join(project_root, "tasks"), task_name),
                " ".join(args)
            ))
            Popen(["/bin/bash", "-c", "#pet {0}={1}\n$SHELL --rcfile {2}\nprintf ''".format(
                project_name,
                amount_active + 1,
                os.path.join(project_root, self.get_rc_filename()),
            )]).communicate()
        else:
            self.make_rc_file(project_name, nr=0, additional_lines=". {0} {1}\nexit\n".format(
                get_file_fullname_and_path(os.path.join(project_root, "tasks"), task_name),
                " ".join(args)
            ))
            Popen(["/bin/bash", "-c", "#pet {0}={1}\n$SHELL --rcfile {2}\nprintf ''".format(
                project_name,
                amount_active + 1,
                os.path.join(project_root, self.get_rc_filename()),
            )]).wait()

    def edit_shell_profiles(self):
        edit_file(os.path.join(get_pet_folder(), BASH_PROFILES_FILENAME))


class Zsh(GeneralShellMixin):

    def __init__(self):
        GeneralShellMixin.__init__(self)
        self.rc_filename = ZSH_RC_FILENAME
        self.shell_profiles = ZSH_PROFILES_FILENAME

    def start(self, project_root, project_name):
        amount_active = how_many_active(project_name)
        self.make_rc_file(project_name, amount_active + 1, additional_lines="")
        Popen(["/bin/sh",
               "-c",
               "#pet {0}={1}\nZDOTDIR={2} $SHELL\nprintf ''".format(
                   project_name,
                   amount_active + 1,
                   project_root,
               )
               ]).communicate()

    def create_shell_profiles(self):
        if not os.path.isfile(os.path.join(get_pet_folder(), ZSH_PROFILES_FILENAME)):
            if os.environ.get('ZDOTDIR', ""):
                with open(os.path.join(get_pet_folder(), ZSH_PROFILES_FILENAME), mode='w') as zsh_profiles:
                    zsh_profiles.write("source $ZDOTDIR/.zshrc\n")
            else:
                with open(os.path.join(get_pet_folder(), ZSH_PROFILES_FILENAME), mode='w') as zsh_profiles:
                    zsh_profiles.write("source $HOME/.zshrc\n")

    @lockable()
    def task_exec(self, project_name, task_name, interactive, args=()):
        amount_active = how_many_active(project_name)
        raise Info("it doesn't work in zsh yet")


@lru_cache()
def get_shell():
    shell_name = os.environ.get('SHELL', '')
    if 'bash' in shell_name:
        shell = Bash()
    elif 'zsh' in shell_name:
        shell = Zsh()
    else:
        raise ShellNotRecognized(
            ExceptionMessages.shell_not_supported.value.format(os.environ.get('SHELL', 'not found $SHELL')))
    return shell


class ProjectLock(object):

    def __init__(self, project_name):

        if not os.path.exists(os.path.join(get_projects_root(), project_name)):
            raise NameNotFound(ExceptionMessages.project_not_found.value.format(project_name))
        self.filepath = os.path.join(get_projects_root(), project_name, "_lock")

    def __enter__(self):
        self.open_file = open(self.filepath, "w")

    def __exit__(self, *args):
        self.open_file.close()
        os.remove(self.filepath)


class ProjectCreator(object):

    def __init__(self, project_name, in_place, templates=()):
        self.projects_root = get_projects_root()
        self.templates_root = get_projects_templates_root()
        self.project_name = project_name
        self.in_place = in_place
        if in_place:
            self.project_root = os.path.join(os.getcwd(), ".pet")
        else:
            self.project_root = os.path.join(self.projects_root, self.project_name)
        self.templates = templates
        self.check_name()
        self.check_templates()

    def check_name(self):
        if project_exist(self.project_name):
            raise NameAlreadyTaken(ExceptionMessages.project_exists.value.format(self.project_name))
        if self.project_name in COMMANDS:
            raise NameAlreadyTaken("{0} - there is pet command with this name, use -n NAME".format(self.project_name))

    def check_templates(self):
        for template in self.templates:
            if not project_template_exist(template):
                raise NameNotFound(ExceptionMessages.template_not_found.value.format(template))

    def create_dirs(self):
        get_shell().create_shell_profiles()
        if not os.path.exists(os.path.join(self.project_root, "tasks")):
            os.makedirs(os.path.join(self.project_root, "tasks"))
        if self.in_place:
            os.symlink(self.project_root, os.path.join(get_projects_root(), self.project_name))
        get_shell().make_rc_file(self.project_name, nr=0)

    def create_additional_files(self):
        with open(os.path.join(self.project_root, "tasks.sh"), mode='w') as tasks_alias_file:
            tasks_alias_file.write("# aliases for your tasks\n")

    def create_files_with_templates(self, filename, additional_lines, increasing_order):
        with open(os.path.join(self.project_root, filename), mode='w') as file:
            if self.templates:
                file.write("# TEMPLATES\n")
                if increasing_order:
                    templates = self.templates
                else:
                    templates = reversed(self.templates)
                for template in templates:
                    file.write("# from template: {0}\n".format(template))
                    with open(os.path.join(self.templates_root, template, filename)) as corresponding_template_file:
                        file.write(corresponding_template_file.read())
                    file.write("\n")
                file.write("# check if correctly imported templates\n")
            file.write(additional_lines)

    def create_files(self):
        add_to_start = new_start_sh_template.format(os.getcwd())
        add_to_stop = "# add here shell code to be executed while exiting project\n"
        self.create_files_with_templates(filename='start.sh', additional_lines=add_to_start, increasing_order=True)
        self.create_files_with_templates(filename='stop.sh', additional_lines=add_to_stop, increasing_order=False)

    def edit(self):
        edit_file(os.path.join(self.project_root, "start.sh"))
        edit_file(os.path.join(self.project_root, "stop.sh"))

    def create(self):
        self.create_dirs()
        self.create_additional_files()
        self.create_files()
        self.edit()


@lockable()
def start(project_name):
    """starts new project"""
    get_shell().create_shell_profiles()
    project_root = os.path.join(get_projects_root(), project_name)
    get_shell().start(project_root, project_name)


def create(project_name, in_place, templates=()):
    """creates new project"""
    ProjectCreator(project_name, in_place, templates).create()


def register(project_name):
    """adds symbolic link to .pet folder in projects"""
    directory = os.getcwd()
    if not project_name:
        project_name = os.path.basename(directory)
    directory = os.path.join(directory, '.pet')
    if project_exist(project_name):
        raise NameAlreadyTaken(ExceptionMessages.project_exists.value.format(project_name))

    if not (os.path.isfile(os.path.join(directory, "start.sh")) and
                os.path.isfile(os.path.join(directory, "stop.sh")) and
                os.path.isfile(os.path.join(directory, "tasks.sh")) and
                os.path.isdir(os.path.join(directory, "tasks"))):
        raise PetException("Haven't found {{tasks.sh, start.sh, stop.sh}} and tasks folder in\n{0}".format(directory))

    os.symlink(directory, os.path.join(get_projects_root(), project_name))
    Popen([
        "/bin/sh",
        "-c",
        "$ sed -i 's/^pet_project_folder=.*$/pet_project_folder='{0}'/g' {1}".format(
            directory,
            os.path.join(directory, "start.sh"),
        ),
    ])


def rename_project(old_project_name, new_project_name):
    """renames projects"""
    projects_root = get_projects_root()
    if not os.path.exists(os.path.join(projects_root, old_project_name)):
        raise NameNotFound(ExceptionMessages.project_not_found.value.format(old_project_name))
    if os.path.exists(os.path.join(projects_root, new_project_name)):
        raise NameAlreadyTaken(ExceptionMessages.project_exists.value.format(new_project_name))
    os.rename(os.path.join(projects_root, old_project_name), os.path.join(projects_root, new_project_name))


def edit_project(project_name):
    """edits project start&stop files"""
    projects_root = get_projects_root()
    if not project_exist(project_name):
        raise NameNotFound(ExceptionMessages.project_not_found.value.format(project_name))

    edit_file(os.path.join(projects_root, project_name, "start.sh"))
    edit_file(os.path.join(projects_root, project_name, "stop.sh"))


def stop():
    """stops project"""
    os.kill(os.getppid(), signal.SIGKILL)


@lockable(check_active=True)
def remove_project(project_name):
    """removes project"""
    project_root = os.path.join(get_projects_root(), project_name)
    if not os.path.exists(project_root):
        raise NameNotFound(ExceptionMessages.project_not_found.value.format(project_name))

    if os.path.islink(project_root):
        os.remove(project_root)
    else:
        shutil.rmtree(project_root)


@lockable(check_active=True)
def archive(project_name):
    """removes project"""
    project_root = os.path.join(get_projects_root(), project_name)
    if not os.path.exists(project_root):
        raise NameNotFound(ExceptionMessages.project_not_found.value.format(project_name))
    if project_name in print_old().split('\n'):
        raise NameAlreadyTaken(ExceptionMessages.project_in_archive.value.format(project_name))

    archive_root = get_archive_root()
    shutil.move(project_root, os.path.join(archive_root, project_name))


def restore(project_name):
    """restores project from archive"""
    if not os.path.exists(os.path.join(get_archive_root(), project_name)):
        raise NameNotFound("{0} - project not found in {1} folder".format(project_name, get_archive_root()))
    if project_exist(project_name):
        raise NameAlreadyTaken(ExceptionMessages.project_exists.value.format(project_name))

    shutil.move(os.path.join(get_archive_root(), project_name), os.path.join(get_projects_root(), project_name))


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
        raise NameNotFound(ExceptionMessages.project_not_found.value.format(project_name))
    if task_exist(project_name, task_name):
        raise NameAlreadyTaken(ExceptionMessages.task_already_exists.value.format(task_name))

    project_root = os.path.join(get_projects_root(), project_name)
    if '.' in task_name:
        task_file_path = os.path.join(project_root, "tasks", task_name)
        task_name = os.path.splitext(task_name)[0]
        Popen(["/bin/sh", "-c", "echo 'add shebang to make sure file will be executable' > {0}".format(task_file_path)])
    else:
        task_file_path = os.path.join(project_root, "tasks", task_name + ".sh")
        Popen(["/bin/sh", "-c", "echo '#!/bin/sh' > {0}".format(task_file_path)])
    edit_file(task_file_path)
    with open(os.path.join(project_root, "tasks.sh"), mode='a') as tasks_alias_file:
        tasks_alias_file.write("alias {0}=\"pet {0}\"\n".format(task_name))
    raise Info("alias available during next boot of project.\nRight now you can invoke it: pet {0}".format(task_name))


def edit_task(project_name, task_name):
    """edits task"""
    if not task_exist(project_name, task_name):
        raise NameNotFound(ExceptionMessages.task_not_found.value.format(task_name))

    edit_file(get_file_fullname_and_path(os.path.join(get_projects_root(), project_name, "tasks"), task_name))


def rename_task(project_name, old_task_name, new_task_name):
    """renames task"""
    tasks_root = os.path.join(get_projects_root(), project_name, "tasks")
    if not task_exist(project_name, old_task_name):
        raise NameNotFound(ExceptionMessages.task_not_found.value.format(old_task_name))
    if task_exist(project_name, new_task_name):
        raise NameAlreadyTaken(ExceptionMessages.task_already_exists.value.format(new_task_name))

    old_task_full_path = get_file_fullname_and_path(tasks_root, old_task_name)
    task_extension = os.path.splitext(old_task_full_path)[1]
    os.rename(old_task_full_path, os.path.join(tasks_root, new_task_name + task_extension))


def run_task(project_name, task_name, interactive, args=()):
    """executes task in correct project"""
    if not task_exist(project_name, task_name):
        raise NameNotFound(ExceptionMessages.task_not_found.value.format(task_name))
    get_shell().create_shell_profiles()
    get_shell().task_exec(project_name, True, task_name, interactive, args)


def remove_task(project_name, task_name):
    """removes task"""
    if not task_exist(project_name, task_name):
        raise NameNotFound("{0}/{1} - task not found in this project".format(project_name, task_name))

    project_root = os.path.join(get_projects_root(), project_name)
    Popen([
        "/bin/sh",
        "-c",
        """
        sed -i -e "/alias {0}/d" {1}
        """.format(
            task_name,
            os.path.join(project_root, "tasks.sh"),
        )
    ])
    os.remove(get_file_fullname_and_path(os.path.join(project_root, "tasks"), task_name))


def edit_config():
    """edits config file using $EDITOR"""
    edit_file(os.path.join(get_pet_folder(), "config"))


def edit_shell_profiles():
    get_shell().edit_shell_profiles()
