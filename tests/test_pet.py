import os
import mock

import pytest

from pet.bl import (
    get_file_fullname,
    get_file_fullname_and_path, check_version, recreate, get_tasks_templates_root, GeneralShellMixin, Bash, get_shell, check_in_active_projects, add_to_active_projects, remove_from_active_projects, get_pet_install_folder, get_pet_folder, \
    get_projects_root, archive, get_archive_root, get_projects_templates_root, get_projects_templates_root, project_template_exist, get_archive_root, edit_file, ProjectLock, \
    ProjectCreator, start, print_projects_for_root, project_exist, task_exist, stop, create, create_task, print_list, print_old, \
    print_tasks, remove_task, restore, rename_project, rename_task, register, clean, edit_project, run_task, edit_task, remove_project,
)
from pet.exceptions import (
    NameAlreadyTaken,
    NameNotFound,
    PetException,
    ProjectActivated,
    ShellNotRecognized,
)

PET_INSTALL_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pet")
PET_FOLDER = os.environ.get('PET_FOLDER', os.path.join(os.path.expanduser("~"), ".pet/"))
projects_root = os.path.join(PET_FOLDER, "projects")
archive_root = os.path.join(PET_FOLDER, "archive")
projects_templates_root = os.path.join(PET_FOLDER, "templates", "projects")
tasks_templates_root = os.path.join(PET_FOLDER, "templates", "tasks")


def lockable_t(check_only_projects=True, check_active=False):
    def _lockable_t(func, *args, **kwargs):
        def __lockable_t(self=None, project_name='', check_only=check_only_projects, *args, **kwargs):
            if self:
                return func(self, project_name, *args, **kwargs)
            else:
                return func(project_name, *args, **kwargs)
        return __lockable_t
    return _lockable_t


@mock.patch('pet.bl.glob.glob')
@mock.patch('os.path.join')
def test_file_fullname_command(mock_join, mock_glob):
    mock_glob.side_effect = [['cancer'], None, ['bigger_cancer']]
    get_file_fullname("", "")
    get_file_fullname("", "")


@mock.patch('pet.bl.glob.glob')
@mock.patch('os.path.join')
def test_get_file_fullname_and_path(mock_join, mock_glob):
    mock_glob.side_effect = [['cancer'], None, ['bigger_cancer']]
    get_file_fullname_and_path("", "")
    get_file_fullname_and_path("", "")


def test_get_pet_install_folder_command():
    assert get_pet_install_folder() == PET_INSTALL_FOLDER


def test_get_pet_folder_command():
    assert get_pet_folder() == PET_FOLDER


@mock.patch('os.path.exists', return_value=True)
def test_get_projects_root_command(mock_exists):
    assert get_projects_root() == projects_root
    mock_exists.assert_called_with(projects_root)


@mock.patch('os.path.exists', return_value=True)
def test_get_projects_templates_root_command(mock_exists):
    assert get_projects_templates_root() == projects_templates_root
    mock_exists.assert_called_with(projects_templates_root)


@mock.patch('os.path.exists', return_value=True)
def test_get_tasks_templates_root_command(mock_exists):
    assert get_tasks_templates_root() == tasks_templates_root
    mock_exists.assert_called_with(tasks_templates_root)


@mock.patch('os.path.exists')
def test_get_archive_root_command(mock_exists):
    assert get_archive_root() == archive_root
    mock_exists.assert_called_with(archive_root)


@mock.patch('os.path.join')
@mock.patch('pet.bl.Popen')
def test_edit_file_command(mock_popen, mock_join, files):
    for path in files:
        edit_file(path)
        mock_popen.assert_called_with([
            "/bin/sh",
            "-c",
            "PET_EDITOR=$(grep '^EDITOR==' {0} | sed -n \"/EDITOR==/s/EDITOR==//p\")\n"
            "if [ -z $PET_EDITOR ]; then\n$EDITOR {1}\n"
            "else\n$PET_EDITOR {1}\nfi".format(mock_join(), path)])


@mock.patch('os.path.exists')
def test_project_exist_command(mock_exists, project_names):
    for project_name in project_names:
        project_exist(project_name)
        project_root = projects_root + "/" + project_name
        mock_exists.assert_called_with(project_root)


@mock.patch('os.path.exists')
def test_template_exist_command(mock_exists, project_names):
    for template_name in project_names:
        project_template_exist(template_name)
        template_root = projects_templates_root + "/" + template_name
        mock_exists.assert_called_with(template_root)


@mock.patch('os.path.splitext')
@mock.patch('pet.bl.print_tasks')
def test_task_exist_command(mock_tasks, mock_split, project_names, task_names):
    for project_name in project_names:
        project_root = projects_root + "/" + project_name
        for task_name in task_names:
            task_exist(project_name, task_name)
            mock_tasks.assert_called_with(project_name)
        task_exist(project_name, "coverage.py")
        mock_tasks.assert_called_with(project_name)


@mock.patch('os.path.join')
@mock.patch('pet.bl.Popen')
def test_add_to_active_projects_command(mock_popen, mock_join, project_names):
    for project_name in project_names:
        add_to_active_projects(project_name)
        mock_popen.assert_called_with(["/bin/sh", "-c", "echo '{0}' >> {1}".format(
            project_name, mock_join())])


@mock.patch('os.path.join')
@mock.patch('pet.bl.check_in_active_projects', return_value="9")
@mock.patch('pet.bl.Popen')
def test_remove_from_active_projects_command(mock_popen, mock_active, mock_join, project_names):
    for project_name in project_names:
        remove_from_active_projects(project_name)
        mock_popen.assert_called_with(["/bin/sh", "-c", "sed -i -e \"{0}d\" {1}".format(
            9, mock_join())])


@mock.patch('pet.bl.PIPE')
@mock.patch('os.path.join')
@mock.patch('pet.bl.Popen')
def test_check_in_active_projects_command(mock_popen, mock_join, mock_pipe, project_names):
    for project_name in project_names:
        check_in_active_projects(project_name)
        mock_popen.assert_called_with(
            ["/bin/sh", "-c", "grep -n ^{0}$ {1} | cut -d \":\" -f 1".format(
            project_name, mock_join())], stdout=mock_pipe)


@mock.patch('pet.bl.PIPE')
@mock.patch('pet.bl.Popen')
def test_check_version_command(mock_popen, mock_pipe):
    check_version()


@mock.patch('pet.bl.makedirs')
@mock.patch('pet.bl.get_pet_folder', return_value=PET_FOLDER)
@mock.patch('pet.bl.get_pet_install_folder', return_value=PET_INSTALL_FOLDER)
@mock.patch('os.path.join')
@mock.patch('pet.bl.Popen')
def test_recreate_command(mock_popen, mock_join, mock_install_folder, mock_pet_folder, mock_makedirs):
    recreate()


@mock.patch('pet.bl.lru_cache')
@mock.patch('os.environ.get')
def test_get_shell_command(mock_get, mock_lru, shells):
    side = shells
    mock_get.side_effect = side
    for i in range(len(shells)):
        assert isinstance(get_shell(), GeneralShellMixin)


@mock.patch('os.path.exists')
@mock.patch('os.remove')
@mock.patch('pet.bl.open')
@mock.patch('os.path.join')
@mock.patch('pet.bl.get_projects_root')
def test_project_lock_class(mock_root, mock_join, mock_open, mock_remove, mock_exists, project_names):
    a = [True] * len(project_names)
    a.append(False)
    mock_exists.side_effect = a
    for project_name in project_names:
        with ProjectLock(project_name):
            mock_open.assert_called_with(mock_join(), "w")
        mock_remove.assert_called_with(mock_join())
    with pytest.raises(NameNotFound):
        ProjectLock("not_existing")


@mock.patch('pet.bl.project_template_exist', return_value=True)
@mock.patch('pet.bl.project_exist', return_value=False)
@mock.patch('pet.bl.get_projects_templates_root', return_value=projects_templates_root)
@mock.patch('pet.bl.get_projects_root', return_value=projects_root)
@mock.patch('os.path.exists', return_value=True)
@mock.patch('os.path.isfile', return_value=True)
@mock.patch('pet.bl.get_shell')
@mock.patch('os.getcwd', return_value="")
@mock.patch('pet.bl.open')
def test_project_creator_class(mock_open, mock_getcwd, mock_shell, mock_isfile, mock_path_exists, mock_root, mock_templates_root, mock_project_exist, mock_template_exist, project_names, additional_project_names):
    for project_name in project_names:
        ProjectCreator(project_name, add_dir=True, templates=additional_project_names).create()


@mock.patch('pet.bl.get_projects_root', return_value=projects_root)
@mock.patch('pet.bl.get_shell')
@mock.patch('os.path.isfile')
def test_start_command(mock_isfile, mock_shell, mock_projects_root, project_names):
    for i, project_name in enumerate(project_names):
        if i == 1:
            mock_isfile.side_effect = [True, True]
            with pytest.raises(ProjectActivated):
                start(project_name)
        else:
            mock_isfile.side_effect = [True, False]
            with pytest.raises(ProjectActivated):
                start(project_name)


@mock.patch('os.getcwd')
@mock.patch('os.path.basename', return_value="project")
@mock.patch('pet.bl.project_exist')
@mock.patch('os.path.isfile')
@mock.patch('os.path.isdir')
@mock.patch('os.symlink')
@mock.patch('os.path.join')
@mock.patch('pet.bl.get_projects_root', return_value=projects_root)
def test_register_command(mock_root, mock_join, mock_symlink, mock_isdir, mock_isfile, mock_exist, mock_basename, mock_getcwd):
    mock_exist.side_effect = [True]
    with pytest.raises(NameAlreadyTaken):
        register("")
    mock_exist.side_effect = [False, False]
    mock_isdir.return_value = True
    mock_isfile.return_value = False
    with pytest.raises(PetException):
        register("")
    mock_isfile.return_value = True
    register("")


@mock.patch('pet.bl.get_projects_root', return_value=projects_root)
@mock.patch('os.path.exists')
@mock.patch('os.rename')
def test_rename_project_command(mock_rename, mock_exists, mock_root, project_names):
    for project_name in project_names:
        mock_exists.side_effect = [False]
        with pytest.raises(NameNotFound):
            rename_project("old", project_name)
        mock_exists.side_effect = [True, True]
        with pytest.raises(NameAlreadyTaken):
            rename_project("old", project_name)
        mock_exists.side_effect = [True, False]
        rename_project("old", project_name)


@mock.patch('pet.bl.get_projects_root', return_value=projects_root)
@mock.patch('pet.bl.project_exist')
@mock.patch('pet.bl.edit_file')
def test_edit_project_command(mock_edit_file, mock_exist, mock_root, project_names):
    for project_name in project_names:
        mock_exist.return_value = False
        with pytest.raises(NameNotFound):
            edit_project(project_name)
        mock_exist.return_value = True
        edit_project(project_name)


@mock.patch('pet.bl.ProjectCreator')
def test_create_command(mock_project_creator, project_names):
    for project_name in project_names:
        create(project_name, add_dir=False, templates=())


@mock.patch('os.kill')
def test_stop_command(mock_kill):
    stop()
    assert mock_kill.called


@mock.patch('pet.bl.lockable', return_value=lockable_t)
@mock.patch('pet.bl.get_projects_root', return_value=projects_root)
@mock.patch('os.path.exists')
@mock.patch('os.path.islink')
@mock.patch('os.remove')
@mock.patch('pet.bl.shutil.rmtree')
def test_remove_project_command(mock_rmtree, mock_remove, mock_islink, mock_exists, mock_root, mock_lockable, project_names):
    for project_name in project_names:
        mock_exists.side_effect = [False]
        with pytest.raises(NameNotFound):
            remove_project(project_name=project_name)
        mock_exists.side_effect = [True, True]
        mock_islink.side_effect = [True, False]
        remove_project(project_name=project_name)
        remove_project(project_name=project_name)


@mock.patch('pet.bl.lockable', return_value=lockable_t)
@mock.patch('pet.bl.get_projects_root', return_value=projects_root)
@mock.patch('os.path.exists')
@mock.patch('pet.bl.shutil.move')
@mock.patch('pet.bl.get_archive_root', return_value=archive_root)
@mock.patch('pet.bl.print_old')
def test_archive_project_command(mock_old, mock_root_archive, mock_move, mock_exists, mock_root, mock_lockable, project_names):
    for project_name in project_names:
        mock_exists.side_effect = [False]
        with pytest.raises(NameNotFound):
            archive(project_name=project_name)
        mock_exists.side_effect = [True, True]
        mock_old.side_effect = [""]
        archive(project_name=project_name)


@mock.patch('pet.bl.shutil.move')
@mock.patch('pet.bl.project_exist')
@mock.patch('pet.bl.get_archive_root', return_value=archive_root)
@mock.patch('pet.bl.get_projects_root', return_value=projects_root)
@mock.patch('os.path.exists')
def test_restore_command(mock_exists, mock_root, mock_archive_root, mock_project_exist, mock_move, project_names):
    for project_name in project_names:
        mock_exists.return_value = False
        with pytest.raises(NameNotFound):
            restore(project_name)
        mock_exists.return_value = True
        mock_project_exist.return_value = True
        with pytest.raises(NameAlreadyTaken):
            restore(project_name)
        mock_project_exist.return_value = False
        restore(project_name)


@mock.patch('pet.bl.get_projects_root', return_value=projects_root)
@mock.patch('os.listdir', return_value=["test_project", "test_project_2", "test_project_3"])
@mock.patch('os.path.exists')
@mock.patch('os.remove')
def test_clean_command(mock_remove, mock_exists, mock_listdir, mock_root):
    clean()
    calls = []
    for project in ["test_project", "test_project_2", "test_project_3"]:
        calls.append(mock.call(os.path.join(projects_root, project, "_lock")))
    for call in calls:
        assert call in mock_remove.mock_calls


@mock.patch('os.listdir', return_value="one\ntwo\nthree")
def test_print_projects_for_root(mock_listdir):
    print_projects_for_root("some root")


@mock.patch('pet.bl.print_projects_for_root')
@mock.patch('pet.bl.get_projects_root', return_value=projects_root)
def test_print_list_command(mock_root, mock_print):
    print_list()
    mock_print.assert_called()


@mock.patch('pet.bl.print_projects_for_root')
@mock.patch('pet.bl.get_projects_root', return_value=projects_root)
def test_print_old_command(mock_root, mock_print):
    print_old()
    mock_print.assert_called()


@mock.patch('pet.bl.print_projects_for_root')
@mock.patch('pet.bl.get_projects_root', return_value=projects_root)
@mock.patch('os.listdir', return_value=['one.txt', 'two.py'])
def test_print_tasks_command(mock_listdir, mock_root, mock_print, project_names):
    for project_name in project_names:
        print_tasks(project_name)


def test_create_task_command(project_names, task_names):
    pass
