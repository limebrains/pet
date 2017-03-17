from unittest import mock
import pytest
import os
from exceptions import NameNotFound, NameAlreadyTaken, ProjectActivated

from bl import get_pet_install_folder, get_pet_folder, create_projects_root, get_projects_root, \
    get_projects_root_or_create, create_archive_root, get_archive_root, get_archive_root_or_create, ProjectLock, \
    TaskExec, ProjectCreator, edit_file, start, project_exist, task_exist, stop, create, create_task, print_list, print_old, \
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


@mock.patch('bl.create_projects_root')
@mock.patch('bl.get_projects_root', side_effect=[None, projects_root, projects_root])
def test_get_projects_root_or_create_command(mock_root, mock_create_root):
    assert get_projects_root_or_create() in ((projects_root, False), (projects_root, True))
    assert get_projects_root_or_create() in ((projects_root, False), (projects_root, True))


@mock.patch('os.makedirs')
def test_create_archive_root_command(mock_makedirs):
    create_archive_root()
    mock_makedirs.assert_called_with(projects_archive)


@mock.patch('os.path.exists')
def test_get_archive_root_command(mock_exists):
    get_archive_root()
    mock_exists.assert_called_with(projects_archive)


@mock.patch('bl.create_archive_root')
@mock.patch('bl.get_archive_root', side_effect=[None, projects_archive, projects_archive])
def test_get_archive_root_or_create_command(mock_root, mock_create_root):
    assert get_archive_root_or_create() in ((projects_archive, False), (projects_archive, True))
    assert get_archive_root_or_create() in ((projects_archive, False), (projects_archive, True))


@mock.patch('bl.get_projects_root', return_value=projects_root)
@mock.patch('os.remove')
@mock.patch('bl.open')
@mock.patch('os.path.isfile', side_effect=[True, False])
@mock.patch('os.path.exists', side_effect=[False, True, True])
def test_project_lock_class(mock_exists, mock_isfile, mock_open, mock_remove, mock_root, project_names):
    for project in project_names:
        project_root = projects_root + "/" + project
        lock = project_root + "/_lock"
        if project == "test_project":
            with pytest.raises(NameNotFound):
                with ProjectLock(project):
                    pass
        elif project == "test_project_2":
            with pytest.raises(ProjectActivated):
                with ProjectLock(project):
                    mock_isfile.assert_called_with(lock)
        else:
            with ProjectLock(project):
                mock_isfile.assert_called_with(lock)
                mock_open.assert_called_with(lock, "w")
            mock_remove.assert_called_with(lock)


@mock.patch('bl.PIPE')
@mock.patch('bl.get_projects_root', return_value=projects_root)
@mock.patch('shutil.copyfile')
@mock.patch('os.remove')
@mock.patch('bl.open')
@mock.patch('bl.Popen')
def test_task_exec_class(mock_popen, mock_open, mock_remove, mock_copyfile, mock_root, mock_pipe, project_names, task_names):
    for project in project_names:
        project_root = projects_root + "/" + project
        shell = "tmp_bashrc"
        filepath = os.path.join(project_root, shell)
        for task in task_names:
            with TaskExec(project, task, shell):
                mock_copyfile.assert_called_with(filepath, filepath + "_task")
                mock_open.assert_called_with(filepath + "_task", mode='a')
                mock_popen.assert_called_with(["/bin/sh", "-c", "$SHELL $1/{0} {1}; $SHELL $1/stop.sh".format(
                    shell + "_task", " ".join(map(str, ()))), project, project_root], stdout=mock_pipe)
            mock_remove.assert_called_with(filepath + "_task")


@mock.patch('bl.get_projects_root', return_value=projects_root)
@mock.patch('bl.project_exist', side_effect=[False, True, True])
@mock.patch('os.path.isfile', side_effect=[False, True, True])
@mock.patch('os.path.exists', side_effect=[False, False, True, True, True, True])
@mock.patch('os.makedirs')
@mock.patch('bl.Popen')
@mock.patch('bl.open')
@mock.patch('bl.edit_file')
def test_project_creator_class(mock_edit_file, mock_open, mock_popen, mock_makedirs, mock_exists, mock_isfile,
                               mock_project_exists, mock_root, project_names, additional_project_names):
    for project in project_names:
        project_root = projects_root + "/" + project
        if project == "test_project":
            with pytest.raises(NameNotFound):
                with ProjectCreator(project, "task").create():
                    pass
        elif project == "test_project_2":
            ProjectCreator(project, templates=additional_project_names).create()
        else:
            ProjectCreator(project).create()


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


@mock.patch('bl.ProjectCreator')
def test_create_command(create_class, project_names, additional_project_names):
    for project in project_names:
        for i in range(len(additional_project_names)):
            create(project, additional_project_names[:i])
            create_class.assert_called_with(project, additional_project_names[:i])


@mock.patch('bl.open')
@mock.patch('os.chmod')
@mock.patch('bl.edit_file')
@mock.patch('bl.Popen')
@mock.patch('bl.task_exist', side_effect=[True, False, False, False, False, False, False, False, False, False, False,
                                          False, False, False, False, False, False, False, False, False, False])
@mock.patch('bl.project_exist', side_effect=[False, True, True, True, True, True, True, True, True, True, True, True,
                                             True, True, True, True, True, True, True, True, True, True, True, True])
def test_create_task_command(mock_project_exist, mock_task_exist, mock_popen, mock_edit_file, mock_chmod, mock_open,
                             project_names, task_names):
    for project in project_names:
        project_root = projects_root + "/" + project
        for task in task_names:
            if task == "hello" and project == "test_project":
                with pytest.raises(NameNotFound):
                    create_task(project, task)
            elif task == "bye" and project == "test_project":
                with pytest.raises(NameAlreadyTaken):
                    create_task(project, task)
            else:
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
@mock.patch('os.path.islink', side_effect=[True, False, True, False])
@mock.patch('os.path.exists', side_effect=[False, True, True, True, False, True, False, True, False, True, False,
                                           True, False, True, False, True, False, True, False, True, False, True])
def test_remove_r_command(mock_exists, mock_islink, mock_remove, mock_rmtree, mock_root,
                          mock_archive, mock_move, project_names):
    answer = "g"
    for project in project_names:
        project_root = projects_root + "/" + project
        if project == "test_project":
            with pytest.raises(NameNotFound):
                remove(project, "A")
            with pytest.raises(ProjectActivated):
                remove(project, "A")
        remove(project, "R")
        assert (mock_remove.called or mock_rmtree.called)
        remove(project, "A")
        assert mock_move.called
        assert remove(project, answer) == "{0} - is not a valid option".format(answer)


@mock.patch('os.remove')
@mock.patch('bl.PIPE')
@mock.patch('bl.Popen')
@mock.patch('bl.task_exist', side_effect=[False, True, True, True, True, True, True, True, True, True, True, True,
                                          True, True, True, True, True, True, True, True, True, True, True, True])
def test_remove_task_command(mock_exist, mock_popen, mock_pipe, mock_remove, project_names, task_names):
    for project in project_names:
        project_root = projects_root + "/" + project
        if project == "test_project":
            with pytest.raises(NameNotFound):
                remove_task(project, "task")
        for task in task_names:
            remove_task(project, task)
            calls = [mock.call(["/bin/sh", "-c", "grep -n \"def {0}\" {1} | cut -d \":\" -f 1".format(
                task, project_root + "/tasks.py")], stdout=mock_pipe),
                     mock.call(["/bin/sh", "-c", "sed -i \"/alias {0}/d\" {1}".format(
                         task, project_root + "/tasks.sh")])]
            for call in calls:
                assert call in mock_popen.mock_calls
            assert mock_remove.called


@mock.patch('bl.get_archive_root', return_value=projects_archive)
@mock.patch('bl.get_projects_root', return_value=projects_root)
@mock.patch('shutil.move')
@mock.patch('os.path.exists', side_effect=[False, True, True, True, True])
def test_restore_command(mock_exists, mock_move, mock_projects_root, mock_archive_root, project_names):
    for project in project_names:
        project_root = os.path.join(projects_root, project)
        project_archive = os.path.join(projects_archive, project)
        if project == "test_project":
            with pytest.raises(NameNotFound):
                restore(project)
        else:
            restore(project)
            mock_move.assert_called_with(project_archive, project_root)


@mock.patch('bl.get_projects_root', return_value="/home/user/pet/projects")
@mock.patch('os.symlink')
@mock.patch('os.path.exists', side_effect=[False, True, True, True, True, True, True])
@mock.patch('bl.project_exist', side_effect=[True, False, False])
@mock.patch('os.getcwd', return_value="/home/user/PycharmProjects/name")
def test_register_command(mock_getcwd, mock_project_exist, mock_exists, mock_symlink, mock_root):
    with pytest.raises(NameAlreadyTaken):
        register()
    assert register() == "Haven't found all 5 files and tasks folder in\n/home/user/PycharmProjects/name"
    register()
    mock_symlink.assert_called_with("/home/user/PycharmProjects/name", "/home/user/pet/projects/name")


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


@mock.patch('bl.get_projects_root', return_value=projects_root)
@mock.patch('os.rename')
@mock.patch('os.path.exists', side_effect=[False, True, True, True, False, True, False, True, False, True, False, True,
                                           False, True, False, True, False, True, False, True, False])
def test_rename_command(mock_exists, mock_rename, mock_root, project_names, additional_project_names):
    for old in project_names:
        old_root = os.path.join(projects_root, old)
        for new in additional_project_names:
            new_root = os.path.join(projects_root, new)
            if old == "test_project" and new == "project_with_templates":
                with pytest.raises(NameNotFound):
                    rename(old, new)
            elif old == "test_project" and new == "project_with_templates_2":
                with pytest.raises(NameAlreadyTaken):
                    rename(old, new)
            else:
                rename(old, new)


@mock.patch('bl.edit_file')
@mock.patch('bl.print_list', return_value=["test_project_2", "test_project_3"])
@mock.patch('bl.get_projects_root', return_value=projects_root)
def test_edit_project_command(mock_root, mock_list, mock_edit_file, project_names):
    for project in project_names:
        if project == "test_project":
            with pytest.raises(NameNotFound):
                edit_project(project)
        else:
            edit_project(project)
            mock_edit_file.assert_called_with(os.path.join(projects_root, project, "stop.sh"))


@mock.patch('bl.get_projects_root', return_value=projects_root)
@mock.patch('bl.task_exist', side_effect=[False, True, True, True, True, True, True, True, True, True, True, True,
                                          True, True, True, True, True, True, True, True, True, True, True, True, True])
@mock.patch('bl.Popen')
@mock.patch('os.path.isfile', side_effect=[True, False, False])
@mock.patch('os.path.exists', side_effect=[False, False, True, True, False, True])
@mock.patch('bl.ProjectLock')
@mock.patch('bl.TaskExec')
def test_run_task_command(mock_task_exec, mock_lock, mock_exists, mock_isfile, mock_popen, mock_task_exist, mock_root,
                          project_names, task_names):
    for project in project_names:
        for task in task_names:
            if project == "test_project":
                if task == task_names[0]:
                    with pytest.raises(NameNotFound):
                        run_task(project, task, None)
                elif task == task_names[1]:
                    run_task(project, task, "test_project")
                    assert mock_popen.called
                elif task == task_names[2]:
                    with pytest.raises(ProjectActivated):
                        run_task(project, task, None)
                elif task == task_names[3]:
                    run_task(project, task, None)
                    assert mock_popen.called
                    assert mock_lock.called
                    assert mock_task_exec.called
                elif task == task_names[4]:
                    run_task(project, task, None)


@mock.patch('bl.get_projects_root', return_value=projects_root)
@mock.patch('bl.task_exist', side_effect=[False, True, True, True, True, True, True, True, True, True, True, True, True,
                                          True, True, True, True, True, True, True, True])
@mock.patch('bl.edit_file')
def test_edit_task_command(mock_edit_file, mock_task_exist, mock_root, project_names, task_names):
    for project in project_names:
        for task in task_names:
            if project == "test_project" and task == "hello":
                with pytest.raises(NameNotFound):
                    edit_task(project, task)
            else:
                edit_task(project, task)
                mock_edit_file.assert_called_with(os.path.join(projects_root, project, "tasks", task + ".sh"))
