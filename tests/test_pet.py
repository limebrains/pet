import os
import mock

import pytest

from pet.bl import (
    get_file_fullname,
    get_file_fullname_and_path, check_in_active_projects, add_to_active_projects, remove_from_active_projects, get_pet_install_folder, get_pet_folder, \
    get_projects_root, get_projects_templates_root, template_exist, get_archive_root, edit_file, ProjectLock, \
    ProjectCreator, start, project_exist, task_exist, stop, create, create_task, print_list, print_old, \
    print_tasks, remove_task, restore, register, clean, edit_project, run_task, edit_task, remove_project
)
from pet.pet_exceptions import (
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


@mock.patch('os.path.exists')
def test_get_archive_root_command(mock_exists):
    assert get_archive_root() == archive_root
    mock_exists.assert_called_with(archive_root)


@mock.patch('pet.bl.Popen')
def test_edit_file_command(Popen, files):
    for path in files:
        edit_file(path)
        Popen.assert_called_with(["/bin/sh", "-c", "$EDITOR %s" % path])


@mock.patch('os.path.exists')
def test_project_exist_command(mock_exists, project_names):
    for project_name in project_names:
        project_exist(project_name)
        project_root = projects_root + "/" + project_name
        mock_exists.assert_called_with(project_root)


@mock.patch('os.path.exists')
def test_template_exist_command(mock_exists, project_names):
    for template_name in project_names:
        template_exist(template_name)
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
def test_add_to_active_projects(mock_popen, mock_join, project_names):
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
def test_check_in_active_projects(mock_popen, mock_join, mock_pipe, project_names):
    for project_name in project_names:
        check_in_active_projects(project_name)
        mock_popen.assert_called_with(
            ["/bin/sh", "-c", "grep -n ^{0}$ {1} | cut -d \":\" -f 1".format(
            project_name, mock_join())], stdout=mock_pipe)


def test_get_shell_command():
    pass


@mock.patch('os.kill')
def test_stop_command(mock_kill):
    stop()
    assert mock_kill.called


@mock.patch('bl.get_projects_root', return_value=projects_root)
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
