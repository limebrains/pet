from unittest import mock
import pytest
import os

from bl import create
from bl import remove
from bl import start
from bl import edit_file


def test_create_command(project_names):
    for name in project_names:
        create(name)
        assert os.path.exists("./projects/%s" % name)
        assert os.path.exists("./projects/%s/project_start" % name)
        assert os.path.exists("./projects/%s/project_stop" % name)


# don't forget to change that!
def test_create_with_templates_command(project_names):
    for name in project_names:
        create(name)
        assert os.path.exists("./projects/%s" % name)
        assert os.path.exists("./projects/%s/project_start" % name)
        assert os.path.exists("./projects/%s/project_stop" % name)


@mock.patch('bl.Popen')
def test_start_command(Popen, project_names):
    for name in project_names:
        assert not os.path.exists("./projects/%s/_lock" % name)
        start(name)
        Popen.assert_called_with(["./start.sh", name, "./projects/%s" % name])
        assert not os.path.exists("./projects/%s/_lock" % name)


@mock.patch('bl.Popen')
def test_edit_file_command(Popen, files):
    for path in files:
        edit_file(path)
        Popen.assert_called_with(["/bin/sh", "-c", "$EDITOR %s" % path])


def test_remove_command(project_names):
    for name in project_names:
        remove(name)
        assert not os.path.exists("./projects/%s" % name)
