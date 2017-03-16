from unittest import mock
import pytest
import os

from bl import get_pet_install_folder, get_pet_folder, create_projects_root, get_projects_root, \
    get_projects_root_or_create, create_archive_root, get_archive_root, get_archive_root_or_create, ProjectLock, \
    TaskExec, Create, edit_file, start, project_exist, task_exist, stop, create, create_task, print_list, print_old, \
    print_tasks, remove, remove_task, restore, register, clean, rename, edit_project, run_task, edit_task
PET_INSTALL_FOLDER = os.path.dirname(os.path.realpath(__file__))
PET_FOLDER = os.environ.get('PET_FOLDER', os.path.join(os.path.expanduser("~"), ".pet/"))
projects_root = PET_FOLDER + "/projects"
projects_archive = PET_FOLDER + "/old"


def test_get_pet_install_folder_command():
    assert get_pet_install_folder() == PET_INSTALL_FOLDER


def test_get_pet_folder_command():
    assert get_pet_folder() == PET_FOLDER


@mock.patch('os.makedirs')
def test_create_projects_root_command(mock_makedirs):
    create_projects_root()
    mock_makedirs.assert_called_with(projects_root)


@mock.patch('os.path.exists')
def test_get_projects_root_command(mock_exists):
    get_projects_root()
    mock_exists.assert_called_with(projects_root)


def test_get_projects_root_or_create_command():
    assert get_projects_root_or_create() in ((projects_root, False), (projects_root, True))


@mock.patch('os.makedirs')
def test_create_archive_root_command(mock_makedirs):
    create_archive_root()
    mock_makedirs.assert_called_with(projects_archive)


@mock.patch('os.path.exists')
def test_get_archive_root_command(mock_exists):
    get_archive_root()
    mock_exists.assert_called_with(projects_archive)


def test_get_archive_root_or_create_command():
    assert get_archive_root_or_create() in ((projects_archive, False), (projects_archive, True))


@mock.patch('os.remove')
@mock.patch('bl.open')
@mock.patch('os.path.isfile', return_value=False)
@mock.patch('os.path.exists')
def test_project_lock_class(mock_exists, mock_isfile, mock_open, mock_remove, project_names):
    for project in project_names:
        project_root = projects_root + "/" + project
        lock = project_root + "/_lock"
        with ProjectLock(project):
            # mock_exists.assert_called_with(project_root)
            # TODO: butt why?
            mock_isfile.assert_called_with(lock)
            mock_open.assert_called_with(lock, "w")
        mock_remove.assert_called_with(lock)


def test_task_exec_class():
    pass


# @mock.patch()
# def test_create_without_templates(project_names):
#     for project in project_names:
#         Create(project)


@mock.patch('bl.Popen')
def test_edit_file_command(Popen, files):
    for path in files:
        edit_file(path)
        Popen.assert_called_with(["/bin/sh", "-c", "$EDITOR %s" % path])


@mock.patch('bl.ProjectLock')
@mock.patch('bl.Popen')
def test_start_command(Popen, ProjectLock, project_names):
    for name in project_names:
        start(name)
        project_root = projects_root + "/" + name
        ProjectLock.assert_called_with(name)
        Popen.assert_called_with([PET_INSTALL_FOLDER + "/boot.sh", name, project_root, PET_INSTALL_FOLDER])


@mock.patch('os.path.exists')
def test_project_exist_command(mock_exists, project_names):
    for project in project_names:
        project_exist(project)
        project_root = projects_root + "/" + project
        mock_exists.assert_called_with(project_root)


@mock.patch('os.path.exists')
def test_task_exist_command(mock_exists, project_names, task_names):
    for project in project_names:
        project_root = projects_root + "/" + project
        for task in task_names:
            task_exist(project, task)
            mock_exists.assert_called_with(project_root + "/tasks/" + task + ".sh")


@mock.patch('os.kill')
def test_stop_command(mock_kill):
    stop()
    assert mock_kill.called


@mock.patch('bl.Create')
def test_create_command(create_class, project_names, additional_project_names):
    for project in project_names:
        for i in range(len(additional_project_names)):
            create(project, additional_project_names[:i])
            create_class.assert_called_with(project, additional_project_names[:i])


# @pytest.mark.skipif(not (str(os.environ.get('WIP', default=False)).lower() in ['true', 't', '1']),
#  reason="I'm workin on that test :)")
@mock.patch('bl.open')
@mock.patch('os.chmod')
@mock.patch('bl.edit_file')
@mock.patch('bl.Popen')
@mock.patch('bl.task_exist', return_value=False)
@mock.patch('bl.project_exist')
def test_create_task_command(mock_project_exist, mock_task_exist, mock_popen, mock_edit_file, mock_chmod, mock_open,
                             project_names, task_names):
    for project in project_names:
        project_root = projects_root + "/" + project
        for task in task_names:
            create_task(project, task)
            mock_popen.assert_called_with(["/bin/sh", "-c", "echo '#!/bin/sh' > {0}".format(
                project_root + "/tasks/" + task + ".sh")])
            mock_edit_file.assert_called_with(project_root + "/tasks/" + task + ".sh")
            mock_chmod.assert_called_with((project_root + "/tasks/" + task + ".sh"), 0o755)
            calls = [mock.call(project_root + "/tasks.py", mode='a'), mock.call(project_root + "/tasks.sh", mode='a')]
            for call in calls:
                assert call in mock_open.mock_calls


@mock.patch('os.path.isdir', return_value=True)
@mock.patch('os.listdir', return_value=["test_project", "test_project_2", "test_project_3"])
def test_print_list_command(mock_listdir, mock_isdir, project_names):
    output = print_list()
    mock_listdir.assert_called_with(projects_root)
    for project in project_names:
        assert project in output


@mock.patch('os.path.isdir', return_value=True)
@mock.patch('os.listdir', return_value=["test_project", "test_project_2", "test_project_3"])
def test_print_old_command(mock_listdir, mock_isdir, project_names):
    output = print_old()
    mock_listdir.assert_called_with(projects_archive)
    for project in project_names:
        assert project in output


@mock.patch('os.listdir', return_value=["hello.py", "bye.py", "task_1.py", "task_2.py", "task_3.py"])
def test_print_tasks_command(mock_listdir, task_names, project_names):
    for project in project_names:
        output = print_tasks(project)
        project_root = projects_root + "/" + project
        mock_listdir.assert_called_with(project_root + "/tasks")
        for task in task_names:
            assert task in output


@mock.patch('shutil.move')
@mock.patch('bl.get_archive_root_or_create', return_value="")
@mock.patch('bl.get_projects_root', return_value="")
@mock.patch('shutil.rmtree')
@mock.patch('os.remove')
@mock.patch('os.path.islink', side_effect=[True, False]*10)
@mock.patch('os.path.exists', side_effect=[True, False]*10)
def test_remove_r_command(mock_exists, mock_islink, mock_remove, mock_rmtree, mock_root,
                          mock_archive, mock_move, project_names):
    for project in project_names:
        project_root = projects_root + "/" + project
        remove(project, "R")
        assert (mock_remove.called or mock_rmtree.called)


@mock.patch('shutil.move')
@mock.patch('bl.get_archive_root_or_create', return_value="")
@mock.patch('bl.get_projects_root', return_value="")
@mock.patch('shutil.rmtree')
@mock.patch('os.remove')
@mock.patch('os.path.islink', side_effect=[True, False]*10)
@mock.patch('os.path.exists', side_effect=[True, False]*10)
def test_remove_a_command(mock_exists, mock_islink, mock_remove, mock_rmtree, mock_root,
                          mock_archive, mock_move, project_names):
    for project in project_names:
        project_root = projects_root + "/" + project
        remove(project, "A")
        assert mock_move.called


@mock.patch('os.remove')
@mock.patch('bl.PIPE')
@mock.patch('bl.Popen')
@mock.patch('bl.task_exist', return_value=True)
def test_remove_task_command(mock_exist, mock_popen, mock_pipe, mock_remove, project_names, task_names):
    for project in project_names:
        project_root = projects_root + "/" + project
        for task in task_names:
            remove_task(project, task)
            calls = [mock.call(["/bin/sh", "-c", "grep -n \"def {0}\" {1} | cut -d \":\" -f 1".format(
                task, project_root + "/tasks.py")], stdout=mock_pipe),
                     mock.call(["/bin/sh", "-c", "sed -i \"/alias {0}/d\" {1}".format(
                         task, project_root + "/tasks.sh")])]
            for call in calls:
                assert call in mock_popen.mock_calls
            assert mock_remove.called
