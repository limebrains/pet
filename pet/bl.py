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
from tabulate import tabulate

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
    new_stop_sh_template,
    edit_file_popen_template,
    auto_complete_zsh_deploy,
    task_exec_template,
)

from pet.utils import makedirs

log = logging.getLogger(__file__)

# TODO: rewrite logging into yields
# TODO: docs with install + gif


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
        choice = output[0]
        dots = output[0].count('.')
        for possible in output:
            if possible.count('.') < dots:
                dots = possible.count('.')
                choice = possible
        return choice
    output = glob.glob(os.path.join(searching_root, file_name))
    if output:
        return output[0]
    output = glob.glob(os.path.join(searching_root, file_name + '.local.*'))
    if output:
        choice = output[0]
        dots = output[0].count('.')
        for possible in output:
            if possible.count('.') < dots:
                dots = possible.count('.')
                choice = possible
        return choice
    output = glob.glob(os.path.join(searching_root, file_name + '.local'))
    if output:
        return output[0]


def get_file_fullname_and_path(searching_root, file_name):
    name = glob.glob(os.path.join(searching_root, file_name + '.*'))
    if name:
        choice = name[0]
        dots = name[0].count('.')
        for possible in name:
            if possible.count('.') < dots:
                dots = possible.count('.')
                choice = possible
        return os.path.join(searching_root, choice)
    name = glob.glob(os.path.join(searching_root, file_name))
    if name:
        return os.path.join(searching_root, name[0])
    name = glob.glob(os.path.join(searching_root, file_name + '.local.*'))
    if name:
        choice = name[0]
        dots = name[0].count('.')
        for possible in name:
            if possible.count('.') < dots:
                dots = possible.count('.')
                choice = possible
        return os.path.join(searching_root, choice)
    name = glob.glob(os.path.join(searching_root, file_name + '.local'))
    if name:
        return os.path.join(searching_root, name[0])


def get_pet_install_folder():
    directory = os.path.dirname(os.path.realpath(__file__))
    if os.path.exists(directory):
        return directory
    else:
        raise FolderNotFound(ExceptionMessages.directory_not_found.value.format(directory))


def get_pet_folder():
    directory = os.path.expanduser(os.environ.get('PET_FOLDER', "~/.pet"))
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
           edit_file_popen_template.format(
                os.path.join(get_pet_folder(), "config"), path)]).communicate()


def project_exist(project_name):
    """checks existence of project"""
    return os.path.exists(os.path.join(get_projects_root(), project_name))


def project_template_exist(template_name):
    """checks existence of project"""
    return os.path.exists(os.path.join(get_projects_templates_root(), template_name))


def task_template_exist(template_name):
    """checks existence of project"""
    return os.path.exists(os.path.join(get_tasks_templates_root(), template_name))


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
    if os.path.isfile(os.path.join(get_pet_folder(), "config")):
        print("Found config file at: {0}".format(os.path.join(get_pet_folder(), "config")))
    else:
        Popen(["/bin/sh",
               "-c",
               "echo \"EDITOR==$EDITOR\" > {0}".format(os.path.join(get_pet_folder(), "config")),
               ])


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

    def make_rc_file(self, project_name, nr, additional_lines="", prompt=""):
        project_root = os.path.join(get_projects_root(), project_name)
        if nr == 1:
            nr = ""
        if not prompt:
            prompt = project_name
        contents = new_project_rc_template.format(
            os.path.join(get_pet_folder(), self.get_shell_profiles()),
            project_name,
            os.path.join(project_root, 'start.sh'),
            nr,
            os.path.join(project_root, 'stop.sh'),
            additional_lines,
            prompt,
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
               "cd {3}\n#pet {0}={1}\n$SHELL --rcfile {2}\nprintf ''".format(
                   project_name,
                   amount_active + 1,
                   os.path.join(project_root, self.get_rc_filename()),
                   project_root,
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
        tasks_root = os.path.join(project_root, "tasks")
        # TODO: delete (tmp)
        os.chmod(get_file_fullname_and_path(tasks_root, task_name), 0o755)
        if interactive:
            self.make_rc_file(project_name, nr=1, additional_lines=task_exec_template.format(
                get_file_fullname_and_path(tasks_root, task_name),
                " ".join(args),
                os.path.join(tasks_root, task_name + ".local.entry.sh"),
                os.path.join(tasks_root, task_name + ".local.exit.sh"),
                "",
            ), prompt=project_name + " - " + task_name)
            Popen(["/bin/bash", "-c", "cd {3}\n#pet {0}={1}\n$SHELL --rcfile {2}\nprintf ''".format(
                project_name,
                amount_active + 1,
                os.path.join(project_root, self.get_rc_filename()),
                project_root,
            )]).communicate()
        else:
            self.make_rc_file(project_name, nr=1, additional_lines=task_exec_template.format(
                get_file_fullname_and_path(os.path.join(project_root, "tasks"), task_name),
                " ".join(args),
                os.path.join(tasks_root, task_name + ".local.entry.sh"),
                os.path.join(tasks_root, task_name + ".local.exit.sh"),
                "exit"
            ), prompt=project_name + " - " + task_name)
            Popen(["/bin/bash", "-c", "cd {3}\n#pet {0}={1}\n$SHELL --rcfile {2}\nprintf ''".format(
                project_name,
                amount_active + 1,
                os.path.join(project_root, self.get_rc_filename()),
                project_root,
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
               "cd {2}\n#pet {0}={1}\nZDOTDIR={2} $SHELL\nprintf ''".format(
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
        project_root = os.path.join(get_projects_root(), project_name)
        tasks_root = os.path.join(project_root, "tasks")
        # TODO: delete (tmp)
        os.chmod(get_file_fullname_and_path(tasks_root, task_name), 0o755)
        if interactive:
            self.make_rc_file(project_name, nr=1, additional_lines=task_exec_template.format(
                get_file_fullname_and_path(tasks_root, task_name),
                " ".join(args),
                os.path.join(tasks_root, task_name + ".local.entry.sh"),
                os.path.join(tasks_root, task_name + ".local.exit.sh"),
                "",
            ), prompt=project_name + " - " + task_name)
            Popen(["/bin/zsh",
                   "-c",
                   "cd {2}\n#pet {0}={1}\nZDOTDIR={2} $SHELL\nprintf ''".format(
                       project_name,
                       amount_active + 1,
                       project_root,
                   )]).communicate()
        else:
            self.make_rc_file(project_name, nr=1, additional_lines=task_exec_template.format(
                get_file_fullname_and_path(os.path.join(project_root, "tasks"), task_name),
                " ".join(args),
                os.path.join(tasks_root, task_name + ".local.entry.sh"),
                os.path.join(tasks_root, task_name + ".local.exit.sh"),
                "exit",
            ), prompt=project_name + " - " + task_name)
            Popen(["/bin/zsh", "-c", "cd {2}\n#pet {0}={1}\nZDOTDIR={2} $SHELL\nprintf ''".format(
                project_name,
                amount_active + 1,
                project_root,
            )]).wait()

    def edit_shell_profiles(self):
        edit_file(os.path.join(get_pet_folder(), ZSH_PROFILES_FILENAME))


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
        self.templates_and_paths = {}
        self.check_name()
        self.check_templates()

    def check_name(self):
        if project_exist(self.project_name):
            raise NameAlreadyTaken(ExceptionMessages.project_exists.value.format(self.project_name))
        if self.project_name in COMMANDS:
            raise NameAlreadyTaken("{0} - there is pet command with this name, use -n NAME".format(self.project_name))

    def check_templates(self):
        for template in self.templates:
            if project_template_exist(template):
                self.templates_and_paths[template] = os.path.join(self.templates_root, template)
            else:
                if project_exist(template):
                    self.templates_and_paths[template] = os.path.join(self.projects_root, template)
                else:
                    raise NameNotFound(ExceptionMessages.template_not_found.value.format(template))

    def create_dirs(self):
        get_shell().create_shell_profiles()
        if not os.path.exists(os.path.join(self.project_root, "tasks")):
            os.makedirs(os.path.join(self.project_root, "tasks"))
        if self.in_place:
            os.symlink(self.project_root, os.path.join(get_projects_root(), self.project_name))
        get_shell().make_rc_file(self.project_name, nr=0)

    def create_locals(self):
        with open(os.path.join(self.project_root, "start.local.entry.sh"), mode='w') as file:
            file.write("# locals\npet_project_folder={0}\n".format(os.getcwd()))
        with open(os.path.join(self.project_root, "start.local.exit.sh"), mode='w') as file:
            file.write("# locals\n")
        with open(os.path.join(self.project_root, "stop.local.entry.sh"), mode='w') as file:
            file.write("# locals\n")
        with open(os.path.join(self.project_root, "stop.local.exit.sh"), mode='w') as file:
            file.write("# locals\n")

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
                    with open(os.path.join(self.templates_and_paths[template], filename)) as corresponding_template_file:
                        file.write(corresponding_template_file.read())
                    file.write("\n")
                file.write("# check if correctly imported templates\n")
            file.write(additional_lines)

    def create_files(self):
        add_to_start = new_start_sh_template
        add_to_stop = new_stop_sh_template
        self.create_files_with_templates(filename='start.sh', additional_lines=add_to_start, increasing_order=True)
        self.create_files_with_templates(filename='stop.sh', additional_lines=add_to_stop, increasing_order=False)

    def edit(self):
        edit_file(os.path.join(self.project_root, "start.sh"))
        edit_file(os.path.join(self.project_root, "stop.sh"))

    def create(self):
        self.create_dirs()
        self.create_locals()
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
                os.path.isdir(os.path.join(directory, "tasks"))):
        raise PetException("Haven't found {{start.sh, stop.sh}} and tasks folder in\n{0}".format(directory))

    os.symlink(directory, os.path.join(get_projects_root(), project_name))
    raise Info("If you want to edit locals do 'pet edit {0} --local".format(project_name))


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


def edit_project_locals(project_name):
    """edits projects local files"""
    projects_root = get_projects_root()
    if not project_exist(project_name):
        raise NameNotFound(ExceptionMessages.project_not_found.value.format(project_name))

    edit_file(os.path.join(projects_root, project_name, "start.local.entry.sh"))
    edit_file(os.path.join(projects_root, project_name, "start.local.exit.sh"))
    edit_file(os.path.join(projects_root, project_name, "stop.local.entry.sh"))
    edit_file(os.path.join(projects_root, project_name, "stop.local.exit.sh"))


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


def add_to_templates(project_name):
    """copy project to templates"""
    project_root = os.path.join(get_projects_root(), project_name)
    if not os.path.exists(project_root):
        raise NameNotFound(ExceptionMessages.project_not_found.value.format(project_name))
    if project_template_exist(project_name):
        raise NameAlreadyTaken(ExceptionMessages.template_exists.value.format(project_name))

    template_root = get_projects_templates_root()
    shutil.copy(project_root, os.path.join(template_root, project_name))


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
    tasks = [os.path.splitext(os.path.splitext(task)[0])[0]
             for task in os.listdir(projects_tasks_root)
             if '.local' not in os.path.splitext(os.path.splitext(task)[0])[0]]
    return "\n".join(tasks)


def print_tree():
    """prints projects and all it's tasks"""
    projects = print_list().splitlines()
    output = []
    for project in projects:
        tasks = print_tasks(project).splitlines()
        if tasks:
            output.append([project, tasks[0]])
            for task in tasks[1:]:
                output.append(["", task])
        else:
            output.append([project, ""])
    return tabulate(output, headers=["Project", "Task"], tablefmt="fancy_grid")


def print_active():
    active_list = Popen([
        "/bin/sh",
        "-c",
        "ps aux | grep \"#pet\" | sed -n \"s/.*#pet\( .*\)=.*/\\1/p\"",
    ], stdout=PIPE
    ).stdout.read()
    return active_list


def print_templates():
    """lists templates"""
    return print_projects_for_root(get_projects_templates_root())


def create_task(project_name, task_name, no_alias, how):
    """creates task"""
    if not project_exist(project_name):
        raise NameNotFound(ExceptionMessages.project_not_found.value.format(project_name))
    if task_exist(project_name, task_name):
        raise NameAlreadyTaken(ExceptionMessages.task_already_exists.value.format(task_name))

    project_root = os.path.join(get_projects_root(), project_name)
    if how == 'save':
        if '.' in task_name:
            task_file_path = os.path.join(project_root, "tasks", task_name)
            task_name = os.path.splitext(task_name)[0]
            Popen(["/bin/sh", "-c", "echo 'add shebang to make sure file will be executable' > {0}".format(task_file_path)])
        else:
            task_file_path = os.path.join(project_root, "tasks", task_name + ".sh")
            Popen(["/bin/sh", "-c", "echo '#!/bin/sh' > {0}".format(task_file_path)])
    elif how == 'local':
        if '.' in task_name:
            task_ext = os.path.splitext(task_name)[1]
            task_name = os.path.splitext(task_name)[0]
            task_file_path = os.path.join(project_root, "tasks", task_name + ".local" + task_ext)
            Popen(["/bin/sh", "-c", "echo 'add shebang to make sure file will be executable' > {0}".format(task_file_path)])
        else:
            task_file_path = os.path.join(project_root, "tasks", task_name + ".local" + ".sh")
            Popen(["/bin/sh", "-c", "echo '#!/bin/sh' > {0}".format(task_file_path)])
    else:
        raise PetException("Choose either --save to save as normal task\neither --local to save as local task")
    edit_file(task_file_path)
    os.chmod(task_file_path, 0o755)
    if no_alias:
        raise Info("You can invoke your task by: pet {0}".format(task_name))
    else:
        if how == 'save':
            alias_file = os.path.join(project_root, "start.sh")
        else:
            alias_file = os.path.join(project_root, "start.local.entry.sh")
        # TODO: find a nice place for this alias to be placed
        with open(alias_file, mode='a') as start_file:
            start_file.write("alias {0}=\"pet {0}\"\n".format(task_name))
        raise Info("alias available during next boot of project.\nRight now you can invoke it: pet {0}".format(task_name))


def edit_task(project_name, task_name):
    """edits task"""
    if not task_exist(project_name, task_name):
        raise NameNotFound(ExceptionMessages.task_not_found.value.format(task_name))

    edit_file(get_file_fullname_and_path(os.path.join(get_projects_root(), project_name, "tasks"), task_name))


def edit_task_locals(project_name, task_name):
    """edits task"""
    if not task_exist(project_name, task_name):
        raise NameNotFound(ExceptionMessages.task_not_found.value.format(task_name))

    tasks_root = os.path.join(get_projects_root(), project_name, "tasks")
    edit_file(os.path.join(tasks_root, task_name + ".local.entry.sh"))
    edit_file(os.path.join(tasks_root, task_name + ".local.exit.sh"))


def rename_task(project_name, old_task_name, new_task_name):
    """renames task"""
    tasks_root = os.path.join(get_projects_root(), project_name, "tasks")
    if not task_exist(project_name, old_task_name):
        raise NameNotFound(ExceptionMessages.task_not_found.value.format(old_task_name))
    if task_exist(project_name, new_task_name):
        raise NameAlreadyTaken(ExceptionMessages.task_already_exists.value.format(new_task_name))

    old_task_full_path = get_file_fullname_and_path(tasks_root, old_task_name)
    task_extension = os.path.splitext(old_task_full_path)[1]
    local = os.path.splitext(os.path.splitext(old_task_full_path)[0])[1]
    os.rename(old_task_full_path, os.path.join(tasks_root, new_task_name + local + task_extension))
    # TODO: look for alias to rename


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
    searching_root = os.path.join(project_root, "tasks")
    if '.local' in get_file_fullname(searching_root, task_name):
        start_file = "start.local.entry.sh"
    else:
        start_file = "start.sh"
    Popen([
        "/bin/sh",
        "-c",
        "sed -i -e \"/alias {0}/d\" {1}".format(
            task_name,
            os.path.join(project_root, start_file),
        )
    ])
    os.remove(get_file_fullname_and_path(searching_root, task_name))


def edit_config():
    """edits config file using $EDITOR"""
    edit_file(os.path.join(get_pet_folder(), "config"))


def edit_shell_profiles():
    get_shell().edit_shell_profiles()


def deploy(shell=''):
    if shell == '':
        shell = os.environ.get('SHELL', '')
    path = os.path.dirname(os.path.realpath(__file__))
    if 'bash' in shell:
        possible = [
            '/etc/bash_completion.d',
            '/usr/local/etc/bash_completion.d',
            '/usr/share/bash-completion/bash_completion',  # this stays last - 1
            os.path.join(os.path.expanduser("~"), '.bash_completion'),  # this stays last
        ]
        available = []
        for directory in possible:
            if os.path.exists(directory):
                available.append(directory)
        if available:
            if available[0] in possible[-2:]:
                with open(available[0], mode='a') as file:
                    file.write(". {0}".format(os.path.join(path, 'complete.bash')))
                raise Info('Deployed auto-completion to {0}'.format(available[0]))
            else:
                with open(os.path.join(available[0], 'pet'), mode='w') as file:
                    file.write(". {0}".format(os.path.join(path, 'complete.bash')))
                raise Info('Deployed auto-completion to {0}'.format(os.path.join(available[0], 'pet')))
        else:
            raise PetException("Haven't found correct path to deploy auto-completions")
    elif 'zsh' in shell:
        rc_path = os.path.join(os.environ.get('ZDOTDIR', os.path.expanduser('~')), '.zshrc')
        with open(rc_path, mode='a') as file:
            file.write(auto_complete_zsh_deploy.format(os.path.join(path, 'complete.bash')))
        raise Info("Auto-completion should work in new zsh terminals")
    else:
        raise ShellNotRecognized(ExceptionMessages.shell_not_supported.value.format(shell))
