import pytest


@pytest.fixture
def project_names():
    return ["test_project", "test_project_2", "test_project_3"]


@pytest.fixture
def task_names():
    return ["hello", "bye", "task_1", "task_2", "task_3"]


@pytest.fixture
def additional_project_names():
    return ["project_with_templates", "project_with_templates_2"]


@pytest.fixture
def file_names():
    return ["project_start", "project_stop"]


@pytest.fixture
def files():
    output = []
    for project in ["test_project", "test_project_2", "test_project_3"]:
        for file_name in ["project_start", "project_stop"]:
            output.append("./%s/%s" % (project, file_name))
    return output


@pytest.fixture
def file_paths():
    return ["./projects/", "test_project_2", "test_project_3"]
