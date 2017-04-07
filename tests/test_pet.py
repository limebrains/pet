import builtins
import os
import mock

import pytest

from pet.bl import (
    get_file_fullname,
    get_file_fullname_and_path, check_version, recreate, get_tasks_templates_root, GeneralShellMixin, Bash, get_shell, get_pet_install_folder, get_pet_folder, \
    get_projects_root, archive, lockable, edit_config, edit_shell_profiles, get_archive_root, get_projects_templates_root, get_projects_templates_root, project_template_exist, get_archive_root, edit_file, ProjectLock, \
    ProjectCreator, start, print_projects_for_root, project_exist, task_exist, stop, create, create_task, print_list, print_old, \
    print_tasks, remove_task, task_template_exist, how_many_active, restore, rename_project, rename_task, register, clean, edit_project, run_task, edit_task, remove_project,
)

from pet.exceptions import (
    ExceptionMessages,
    NameAlreadyTaken,
    NameNotFound,
    PetException,
    ProjectActivated,
    Info,
    ShellNotRecognized,
    FolderNotFound,
)

from pet.file_templates import (
    edit_file_popen_template,
    new_project_rc_template,
    new_start_sh_template,
    auto_complete_zsh_deploy,
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
def test_file_fullname_command(mock_glob):
    mock_glob.return_value = ['cancer.sh']
    searching_root = "searching_here"
    file_name = "file_without_ext"
    assert get_file_fullname(searching_root, file_name) == 'cancer.sh'
    mock_glob.assert_called_with(os.path.join(searching_root, file_name + '.*'))
    mock_glob.side_effect = [None, ['bigger_cancer.sh']]
    assert get_file_fullname(searching_root, file_name) == 'bigger_cancer.sh'
    mock_glob.assert_called_with(os.path.join(searching_root, file_name))


@mock.patch('pet.bl.glob.glob')
def test_get_file_fullname_and_path(mock_glob):
    mock_glob.return_value = ['cancer.sh']
    searching_root = "searching_here"
    file_name = "file_without_ext"
    assert get_file_fullname_and_path(searching_root, file_name) == searching_root + '/cancer.sh'
    mock_glob.assert_called_with(os.path.join(searching_root, file_name + '.*'))
    mock_glob.side_effect = [None, ['bigger_cancer.sh']]
    assert get_file_fullname_and_path(searching_root, file_name) == searching_root + '/bigger_cancer.sh'
    mock_glob.assert_called_with(os.path.join(searching_root, file_name))


@mock.patch('os.path.dirname')
@mock.patch('os.path.exists')
def test_get_pet_install_folder_command(mock_exists, mock_dirname):
    mock_dirname.return_value = PET_INSTALL_FOLDER
    mock_exists.return_value = True
    assert get_pet_install_folder() == PET_INSTALL_FOLDER
    mock_exists.assert_called_with(PET_INSTALL_FOLDER)
    mock_exists.return_value = False
    with pytest.raises(FolderNotFound):
        get_pet_install_folder()


@mock.patch('os.path.expanduser')
@mock.patch('os.path.exists')
def test_get_pet_folder_command(mock_exists, mock_expand):
    mock_expand.return_value = PET_FOLDER
    mock_exists.return_value = True
    assert get_pet_folder() == PET_FOLDER
    mock_exists.assert_called_with(PET_FOLDER)
    mock_exists.return_value = False
    with pytest.raises(FolderNotFound):
        get_pet_folder()


@mock.patch('pet.bl.get_pet_folder', return_value=PET_FOLDER)
@mock.patch('os.path.exists', return_value=True)
def test_get_projects_root_command(mock_exists, mock_get_pet_folder):
    mock_exists.return_value = True
    assert get_projects_root() == projects_root
    mock_exists.assert_called_with(projects_root)
    mock_exists.return_value = False
    with pytest.raises(FolderNotFound):
        get_projects_root()


@mock.patch('pet.bl.get_pet_folder', return_value=PET_FOLDER)
@mock.patch('os.path.exists', return_value=True)
def test_get_projects_templates_root_command(mock_exists, mock_get_pet_folder):
    mock_exists.return_value = True
    assert get_projects_templates_root() == projects_templates_root
    mock_exists.assert_called_with(projects_templates_root)
    mock_exists.return_value = False
    with pytest.raises(FolderNotFound):
        get_projects_templates_root()


@mock.patch('pet.bl.get_pet_folder', return_value=PET_FOLDER)
@mock.patch('os.path.exists', return_value=True)
def test_get_tasks_templates_root_command(mock_exists, mock_get_pet_folder):
    mock_exists.return_value = True
    assert get_tasks_templates_root() == tasks_templates_root
    mock_exists.assert_called_with(tasks_templates_root)
    mock_exists.return_value = False
    with pytest.raises(FolderNotFound):
        get_tasks_templates_root()


@mock.patch('pet.bl.get_pet_folder', return_value=PET_FOLDER)
@mock.patch('os.path.exists')
def test_get_archive_root_command(mock_exists, mock_get_pet_folder):
    mock_exists.return_value = True
    assert get_archive_root() == archive_root
    mock_exists.assert_called_with(archive_root)
    mock_exists.return_value = False
    with pytest.raises(FolderNotFound):
        get_archive_root()


@mock.patch('pet.bl.get_pet_folder', return_value=PET_FOLDER)
@mock.patch('os.path.join')
@mock.patch('pet.bl.Popen')
def test_edit_file_command(mock_popen, mock_join, mock_get_pet_folder, files):
    path = files[0]
    edit_file(path)
    mock_popen.assert_called_with([
        "/bin/sh",
        "-c",
        edit_file_popen_template.format(mock_join(), path)])


@mock.patch('pet.bl.get_projects_root', return_value=projects_root)
@mock.patch('os.path.exists')
def test_project_exist_command(mock_exists, mock_projects_root, project_names):
    project_name = project_names[0]
    mock_exists.return_value = True
    assert project_exist(project_name)
    project_root = os.path.join(projects_root, project_name)
    mock_exists.assert_called_with(project_root)
    mock_exists.return_value = False
    assert not project_exist(project_name)
    mock_exists.assert_called_with(project_root)


@mock.patch('pet.bl.get_projects_templates_root', return_value=projects_templates_root)
@mock.patch('os.path.exists')
def test_template_exist_command(mock_exists, mock_templates_root, project_names):
    template_name = project_names[0]
    mock_exists.return_value = True
    assert project_template_exist(template_name)
    template_root = os.path.join(projects_templates_root, template_name)
    mock_exists.assert_called_with(template_root)
    mock_exists.return_value = False
    assert not project_template_exist(template_name)
    mock_exists.assert_called_with(template_root)


@mock.patch('pet.bl.get_tasks_templates_root', return_value=tasks_templates_root)
@mock.patch('os.path.exists')
def test_task_template_exist_command(mock_exists, mock_templates_root, task_names):
    template_name = task_names[0]
    mock_exists.return_value = True
    assert task_template_exist(template_name)
    template_root = os.path.join(tasks_templates_root, template_name)
    mock_exists.assert_called_with(template_root)
    mock_exists.return_value = False
    assert not task_template_exist(template_name)
    mock_exists.assert_called_with(template_root)


@mock.patch('pet.bl.print_tasks')
def test_task_exist_command(mock_tasks, project_names, task_names):
    project_name = project_names[0]
    task_name = task_names[0]
    mock_tasks.return_value = "{0}\ntask1\ntask2\ncov\n".format(task_name)
    assert task_exist(project_name, task_name)
    mock_tasks.assert_called_with(project_name)
    task_exist(project_name, "coverage.py")
    assert not mock_tasks.assert_called_with(project_name)


# TODO: MOCKING methods of already mocked objects
@mock.patch('pet.bl.PIPE')
@mock.patch('pet.bl.Popen')
def test_how_many_active_command(mock_popen, mock_pipe, project_names):
    process_mock = mock.Mock()
    attrs = {'stdout.read.return_value': '1\n2\n3\n'}
    process_mock.configure_mock(**attrs)
    mock_popen.return_value = process_mock
    project_name = project_names[0]
    assert how_many_active(project_name) == 3
    attrs = {'stdout.read.return_value': ''}
    process_mock.configure_mock(**attrs)
    assert how_many_active(project_name) == 0


@mock.patch('pet.bl.PIPE')
@mock.patch('pet.bl.Popen')
def test_check_version_command(mock_popen, mock_pipe):
    process_mock = mock.Mock()
    attrs = {'stdout.read.return_value': '3.4.5\n'}
    process_mock.configure_mock(**attrs)
    mock_popen.return_value = process_mock
    assert check_version() == '3.4.5'


@mock.patch('pet.bl.makedirs')
@mock.patch('pet.bl.get_pet_folder', return_value=PET_FOLDER)
@mock.patch('os.path.join')
@mock.patch('pet.bl.Popen')
def test_recreate_command(mock_popen, mock_join, mock_pet_folder, mock_makedirs):
    recreate()
    mock_popen.assert_called_with(["/bin/sh",
                                   "-c",
                                   "echo \"EDITOR==$EDITOR\" > {0}".format(os.path.join(PET_FOLDER, "config")),
                                   ])


@mock.patch('pet.bl.ProjectLock')
@mock.patch('pet.bl.log.warning')
@mock.patch('pet.bl.how_many_active')
@mock.patch('pet.bl.get_pet_folder', return_value=PET_FOLDER)
@mock.patch('os.path.isfile')
def test_lockable_decorator(mock_isfile, mock_pet_folder, mock_amount_active, mock_log_warning, mock_project_lock, project_names):
    name = project_names[0]

    @lockable()
    def func_to_test1(project_name):
        pass
    mock_isfile.return_value = True
    with pytest.raises(ProjectActivated):
        func_to_test1(project_name=name)

    @lockable(check_active=True)
    def func_to_test2(project_name):
        pass
    mock_isfile.return_value = False
    mock_amount_active.return_value = 3
    with pytest.raises(ProjectActivated):
        func_to_test2(project_name=name)

    @lockable(check_only_projects=False)
    def func_to_test3(project_name, arg1, arg2, kwarg=''):
        return project_name, arg1, arg2, kwarg
    assert func_to_test3(project_name=name, arg1=1, arg2=2, kwarg='x') == (name, 1, 2, 'x')
    mock_log_warning.assert_called_with(ExceptionMessages.project_is_active.value.format(name))
    assert mock_project_lock.called

    @lockable()
    def func_to_test4(project_name, arg1, arg2, kwarg=''):
        return project_name, arg1, arg2, kwarg

    assert func_to_test4(project_name=name, arg1=1, arg2=2, kwarg='x') == (name, 1, 2, 'x')

    assert func_to_test4(project_name=name, arg1=1, arg2=2, kwarg='x', lock=True) == (name, 1, 2, 'x')
    mock_log_warning.assert_called_with(ExceptionMessages.project_is_active.value.format(name))

    class ClassToTest1(object):

        def __init__(self, arg1, arg2, kwarg=''):
            self.arg1 = arg1
            self.arg2 = arg2
            self.kwarg = kwarg

        @lockable(check_only_projects=False)
        def action(self, project_name):
            arg3 = self.arg1 + self.arg2
            return project_name, self.arg1, self.arg2, arg3, self.kwarg

    assert ClassToTest1(arg1=1, arg2=2, kwarg='x').action(project_name=name) == (name, 1, 2, 3, 'x')

    class ClassToTest2(object):
        def __init__(self, arg1, arg2, kwarg=''):
            self.arg1 = arg1
            self.arg2 = arg2
            self.kwarg = kwarg

        @lockable()
        def action(self, project_name):
            arg3 = self.arg1 + self.arg2
            return project_name, self.arg1, self.arg2, arg3, self.kwarg

    assert ClassToTest2(arg1=1, arg2=2, kwarg='x').action(project_name=name) == (name, 1, 2, 3, 'x')

    assert ClassToTest2(arg1=1, arg2=2, kwarg='x').action(project_name=name, lock=True) == (name, 1, 2, 3, 'x')
    mock_log_warning.assert_called_with(ExceptionMessages.project_is_active.value.format(name))


# TODO: 7th


# TODO: MOCKING MOCK_OPEN
@mock.patch('pet.bl.get_pet_folder', return_value=PET_FOLDER)
@mock.patch('pet.bl.get_projects_root', return_value=projects_root)
def test_general_shell_mixin_make_rc_file_method(mock_root, mock_pet_folder, project_names):
    project_name = project_names[0]
    project_root = os.path.join(get_projects_root(), project_name)
    nr = 0
    additional_lines = ""
    rc = os.path.join(project_root, "bashrc")
    with mock.patch('builtins.open', create=True) as mock_open:
        Bash().make_rc_file(project_name, nr)
        mock_open.assert_called_with(rc, mode='w')
        handle = mock_open.return_value.__enter__.return_value
        handle.write.assert_called_with(
            new_project_rc_template.format(
                os.path.join(PET_FOLDER, "bash_profiles"),
                project_name,
                os.path.join(project_root, 'start.sh'),
                nr,
                os.path.join(project_root, "tasks.sh"),
                os.path.join(project_root, 'stop.sh'),
                additional_lines,
            )
        )
    nr = 1
    additional_lines = "cancerous line"
    with mock.patch('builtins.open', create=True) as mock_open:
        Bash().make_rc_file(project_name, nr, additional_lines)
        mock_open.assert_called_with(rc, mode='w')
        handle = mock_open.return_value.__enter__.return_value
        handle.write.assert_called_with(
            new_project_rc_template.format(
                os.path.join(PET_FOLDER, "bash_profiles"),
                project_name,
                os.path.join(project_root, 'start.sh'),
                "",
                os.path.join(project_root, "tasks.sh"),
                os.path.join(project_root, 'stop.sh'),
                additional_lines,
            )
        )


@mock.patch('os.environ.get', return_value='wrong/shell')
def test_general_shell_mixin_class_errors(mock_get, project_names, task_names):
    project_name = project_names[0]
    task_name = task_names[0]
    project_root = os.path.join(projects_root, project_name)
    with pytest.raises(ShellNotRecognized):
        GeneralShellMixin().start(project_root, project_name)
    with pytest.raises(ShellNotRecognized):
        GeneralShellMixin().create_shell_profiles()
    with pytest.raises(ShellNotRecognized):
        GeneralShellMixin().task_exec(project_name, task_name, interactive=False)
    with pytest.raises(ShellNotRecognized):
        GeneralShellMixin().edit_shell_profiles()


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
    mock_exists.return_value = True
    project_name = project_names[0]
    with ProjectLock(project_name):
        mock_open.assert_called_with(mock_join(), "w")
    mock_remove.assert_called_with(mock_join())
    mock_exists.return_value = False
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
@mock.patch('os.symlink')
@mock.patch('pet.bl.open')
def test_project_creator_class(mock_open, mock_symlink, mock_getcwd, mock_shell, mock_isfile, mock_path_exists, mock_root, mock_templates_root, mock_project_exist, mock_template_exist, project_names, additional_project_names):
    project_name = project_names[0]
    ProjectCreator(project_name, in_place=False, templates=[additional_project_names[0], additional_project_names[1]]).create()


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
        create(project_name, in_place=False, templates=())


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


@mock.patch('pet.bl.project_exist')
@mock.patch('pet.bl.task_exist')
@mock.patch('pet.bl.get_projects_root', return_value=projects_root)
@mock.patch('pet.bl.Popen')
@mock.patch('pet.bl.edit_file')
@mock.patch('pet.bl.open')
def test_create_task_command(mock_open, mock_edit_file, mock_popen, mock_root, mock_task_exist, mock_project_exist, project_names, task_names):
    for project_name in project_names:
        mock_project_exist.return_value = False
        with pytest.raises(NameNotFound):
            create_task(project_name, task_names[0])
        mock_project_exist.return_value = True
        mock_task_exist.return_value = True
        with pytest.raises(NameAlreadyTaken):
            create_task(project_name, task_names[0])
        mock_project_exist.return_value = True
        mock_task_exist.return_value = False
        with pytest.raises(Info):
            create_task(project_name, task_names[0])


@mock.patch('pet.bl.get_projects_root', return_value=projects_root)
@mock.patch('pet.bl.get_file_fullname_and_path')
@mock.patch('pet.bl.edit_file')
@mock.patch('pet.bl.task_exist')
def test_edit_task_command(mock_exist, mock_edit, mock_fullpath, mock_root, project_names, task_names):
    for project_name in project_names:
        for task_name in task_names:
            mock_exist.return_value = False
            with pytest.raises(NameNotFound):
                edit_task(project_name, task_name)
            mock_exist.return_value = True
            edit_task(project_name, task_name)


@mock.patch('pet.bl.get_projects_root', return_value=projects_root)
@mock.patch('pet.bl.get_file_fullname_and_path', return_value='sth.ext')
@mock.patch('pet.bl.task_exist')
@mock.patch('os.rename')
def test_rename_task_command(mock_rename, mock_task_exist, mock_fullpath, mock_root, project_names, task_names):
    for project_name in project_names:
        mock_task_exist.side_effect = [False]
        with pytest.raises(NameNotFound):
            rename_task(project_name, task_names[0], task_names[1])
        mock_task_exist.side_effect = [True, True]
        with pytest.raises(NameAlreadyTaken):
            rename_task(project_name, task_names[0], task_names[1])
        mock_task_exist.side_effect = [True, False]
        rename_task(project_name, task_names[0], task_names[1])


@mock.patch('pet.bl.get_shell')
@mock.patch('os.path.isfile')
@mock.patch('pet.bl.task_exist')
def test_run_task_command(mock_exist, mock_isfile, mock_shell, project_names, task_names):
    for project_name in project_names:
        mock_exist.return_value = False
        with pytest.raises(NameNotFound):
            run_task(project_name, task_names[0], interactive=False, args=())
        mock_exist.return_value = True
        mock_isfile.return_value = False
        run_task(project_name, task_names[0], interactive=False, args=())


@mock.patch('pet.bl.get_file_fullname_and_path')
@mock.patch('pet.bl.get_projects_root', return_value=projects_root)
@mock.patch('pet.bl.task_exist')
@mock.patch('pet.bl.Popen')
@mock.patch('pet.bl.PIPE')
@mock.patch('os.remove')
def test_remove_task_command(mock_remove, mock_pipe, mock_popen, mock_exist, mock_root, mock_fullpath, project_names, task_names):
    for project_name in project_names:
        mock_exist.return_value = False
        with pytest.raises(NameNotFound):
            remove_task(project_name, task_names[0])
        mock_exist.return_value = True
        mock_popen.stdout.read().return_value = b'6\n'
        remove_task(project_name, task_names[0])


@mock.patch('pet.bl.get_pet_install_folder', return_value=PET_INSTALL_FOLDER)
@mock.patch('pet.bl.Popen')
def test_edit_config_command(mock_popen, mock_folder):
    edit_config()


@mock.patch('pet.bl.get_pet_install_folder', return_value=PET_INSTALL_FOLDER)
@mock.patch('pet.bl.edit_file')
def test_edit_config_command(mock_edit, mock_folder):
    edit_shell_profiles()
