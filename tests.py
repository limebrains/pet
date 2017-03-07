from unittest import mock
import pytest
import os

from bl import create
from bl import remove
from bl import start

name = "testing_project"


def test_create_command():
    create(name)
    assert os.path.exists("./projects/%s" % name)
    assert os.path.exists("./projects/%s/project_start" % name)
    assert os.path.exists("./projects/%s/project_stop" % name)


@mock.patch('bl.Popen')
def test_start_command(Popen):
    assert not os.path.exists("./projects/%s/_lock" % name)
    start(name)
    Popen.assert_called_with(["./start.sh", name, "./projects/%s" % name])
    assert not os.path.exists("./projects/%s/_lock" % name)


def test_remove_command():
    remove(name)
    assert not os.path.exists("./projects/%s" % name)
