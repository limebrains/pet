from unittest import mock
import pytest
import os

from bl import create
from bl import remove
from bl import start
from bl import edit_file
from bl import get_pet_install_folder
from bl import get_projects_root


def test_create_command(project_names):
    for name in project_names:
        create(name)
        assert os.path.exists("./projects/%s" % name)
        assert os.path.exists("./projects/%s/start.sh" % name)
        assert os.path.exists("./projects/%s/stop.sh" % name)


@mock.patch('bl.Popen')
def test_start_command(Popen, project_names):
    for name in project_names:
        assert not os.path.exists("./projects/%s/_lock" % name)
        start(name)
        Popen.assert_called_with([os.path.join(get_pet_install_folder(), "boot.sh"), name, os.path.join(
            get_projects_root(), name), get_pet_install_folder()])
        assert not os.path.exists("./projects/%s/_lock" % name)


@mock.patch('bl.Popen')
def test_edit_file_command(Popen, files):
    for path in files:
        edit_file(path)
        Popen.assert_called_with(["/bin/sh", "-c", "$EDITOR %s" % path])


def test_remove_command(project_names):
    for name in project_names:
        remove(name, "R")
        assert not os.path.exists("./projects/%s" % name)
