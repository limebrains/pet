from subprocess import Popen, PIPE
import os
import signal
import shutil
from exceptions import NameAlreadyTaken, NameNotFound, ProjectActivated
from file_templates import new_tasks_file, new_project_py_file, new_task


PET_INSTALL_FOLDER = os.path.dirname(os.path.realpath(__file__))
# TODO: move boot.sh and create_shell.sh to python
# TODO: tests!!!
PET_FOLDER = os.environ.get('PET_FOLDER', os.path.join(os.path.expanduser("~"), ".pet/"))


def create_projects_root():
    os.makedirs(os.path.join(PET_FOLDER, "projects"))


def get_projects_root():
    if os.path.exists(os.path.join(PET_FOLDER, "projects")):
        return os.path.join(PET_FOLDER, "projects")


def get_projects_root_or_create():
    project_root = get_projects_root()
    if not project_root:
        create_projects_root()
        return get_projects_root(), True
    return project_root, False


def create_archive_root():
    os.makedirs(os.path.join(PET_FOLDER, "old"))


def get_archive_root():
    if os.path.exists(os.path.join(PET_FOLDER, "old")):
        return os.path.join(PET_FOLDER, "old")


def get_archive_root_or_create():
    archive_root = get_archive_root()
    if not archive_root:
        create_archive_root()
        return get_archive_root(), True
    return archive_root, False


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

    def __init__(self, name, task, shell, args=()):

        project_root = os.path.join(get_projects_root(), name)
        self.filepath = os.path.join(project_root, shell)
        shutil.copyfile(self.filepath, self.filepath + "_task")
        with open(self.filepath + "_task", mode='a') as work_shell:
            work_shell.write("source {0}\n".format(os.path.join(project_root, "tasks", task + ".sh")))
        self.out = Popen(["/bin/sh", "-c", "$SHELL $1/{0} {1}; $SHELL $1/stop.sh".format(
            shell + "_task", " ".join(map(str, args))),
                          name, project_root], stdout=PIPE).stdout.read()

    def __enter__(self):
        pass

    def __exit__(self, *args):
        os.remove(self.filepath + "_task")
        print(self.out.decode("utf-8"))


def edit_file(path):
    """edits file using $EDITOR"""
    Popen(["/bin/sh", "-c", "$EDITOR {0}".format(path)]).communicate(input)


def start(name):
    """starts new project"""
    with ProjectLock(name=name):
        Popen([os.path.join(PET_INSTALL_FOLDER, "boot.sh"), name, os.path.join(get_projects_root(), name),
               PET_INSTALL_FOLDER]).communicate(input)


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
    projects_root = get_projects_root()
    for template in templates:
        if not project_exist(template):
            raise NameNotFound("{0} - template not found".format(template))
    if not os.path.isfile(os.path.join(PET_INSTALL_FOLDER, "shell_profiles")):
        Popen(os.path.join(PET_INSTALL_FOLDER, "create_shell.sh"))
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
                start_file.write("# from template: {0}\n".format(template))
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
                stop_file.write("# from template: {0}\n".format(template))
                template_stop_file = open(os.path.join(projects_root, template, "stop.sh"))
                stop_file.write(template_stop_file.read())
                stop_file.write("\n")
            stop_file.write("# check if correctly imported templates\n")
        else:
            stop_file.write('# add here shell code to be executed while exiting project\n')
    with open(os.path.join(projects_root, name, "tasks.sh"), mode='w') as tasks_alias_file:
        tasks_alias_file.write("# aliases for your tasks\n")
    edit_file(os.path.join(projects_root, name, "start.sh"))
    edit_file(os.path.join(projects_root, name, "stop.sh"))


def create_task(project, name):
    """creates task"""
    if project_exist(project):
        if not task_exist(project, name):
            projects_root = get_projects_root()
            Popen(["/bin/sh", "-c", "echo '#!/bin/sh' > {0}".format(os.path.join(projects_root, project, "tasks",
                                                                                 name + ".sh"))]).communicate(input)
            edit_file(os.path.join(projects_root, project, "tasks", name + ".sh"))
            os.chmod(os.path.join(projects_root, project, "tasks", name + ".sh"), 0o755)
            with open(os.path.join(projects_root, project, "tasks.py"), mode='a') as tasks_file:
                tasks_file.write(new_task.format(name, project, name))
            with open(os.path.join(projects_root, project, "tasks.sh"), mode='a') as tasks_alias_file:
                tasks_alias_file.write("alias {0}=\"pet {0}\"\n".format(name))
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
    projects_root = get_archive_root_or_create()
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


def remove(name):
    """removes project"""
    projects_root = get_projects_root()
    if os.path.exists(os.path.join(projects_root, name)):
        if not os.path.exists(os.path.join(projects_root, name, "_lock")):
            print("(A) - Archive\n(R) - Remove")
            answer = input()
            if answer == "A" or answer == "a":
                archive = get_archive_root_or_create()
                shutil.move(os.path.join(projects_root, name), os.path.join(archive, name))
            elif answer == "R" or answer == "r":
                if os.path.islink(os.path.join(projects_root, name)):
                    os.remove(os.path.join(projects_root, name))
                else:
                    shutil.rmtree(os.path.join(projects_root, name))
            else:
                print("{0} - is not a valid option".format(answer))
        else:
            raise ProjectActivated("{0} - project is active".format(name))
    else:
        raise NameNotFound("{0} - project not found".format(name))


def remove_task(project, task):
    """removes task"""
    if task_exist(project, task):
        project_root = os.path.join(get_projects_root(), project)
        num = Popen(["/bin/sh", "-c", "grep -n \"def {0}\" {1} | cut -d \":\" -f 1".format(
            task, os.path.join(project_root, "tasks.py"))], stdout=PIPE).stdout.read()
        num = int(num.decode("utf-8")[:-1])
        Popen(["/bin/sh", "-c", "sed -i -e \"{0},{1}d\" {2}".format(
            str(num-3), str(num+2), os.path.join(project_root, "tasks.py"))])
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
                os.path.exists(os.path.join(folder, "tasks.sh")) and
                os.path.exists(os.path.join(folder, "tasks.py")) and
                os.path.exists(os.path.join(folder, "tasks"))):
            os.symlink(folder, os.path.join(get_projects_root(), name))
        else:
            print("Haven't found all 5 files and tasks folder in\n{0}".format(folder))
    else:
        raise NameAlreadyTaken("{0} - name already taken".format(name))


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
        popen_args = [os.path.join(get_projects_root(), project, "tasks", task + ".sh")]
        popen_args.extend(list(args))
        if active == project:
            Popen(popen_args)
        else:
            if os.path.isfile(os.path.join(get_projects_root(), project, "_lock")):
                raise ProjectActivated("{0} - project already activated".format(project))
            project_root = os.path.join(get_projects_root(), project)
            if not os.path.exists(os.path.join(project_root, "tmp_bashrc")) and \
                    not os.path.exists(os.path.join(project_root, ".zshrc")):
                Popen([os.path.join(PET_INSTALL_FOLDER, "boot.sh"), project, project_root,
                       PET_INSTALL_FOLDER])
            with ProjectLock(name=project):
                if os.path.exists(os.path.join(project_root, "tmp_bashrc")):
                    with TaskExec(project, task, "tmp_bashrc", list(args)):
                        pass
                elif os.path.exists(os.path.join(project_root, ".zshrc")):
                    with TaskExec(project, task, ".zshrc", list(args)):
                        pass
    else:
        raise NameNotFound("{0} - task not found".format(task))


def edit_task(project, task):
    """edits task"""
    if task_exist(project, task):
        edit_file(os.path.join(get_projects_root(), project, "tasks", task + ".sh"))
    else:
        raise NameNotFound("{0} - task not found".format(task))
