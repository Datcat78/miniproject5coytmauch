# INF601 - Advanced Programming in Python
# Coyt Mauch
# Mini Project 5

import os
import re

import pytest

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(PROJECT_DIR, "tasktracker", "templates")
HEADER = "# INF601 - Advanced Programming in Python\n# Coyt Mauch\n# Mini Project 5\n"


def project_files(folder, extension):
    """Paths of every file with this extension under a project folder."""
    for root, _dirs, files in os.walk(os.path.join(PROJECT_DIR, folder)):
        for name in files:
            if name.endswith(extension):
                yield os.path.join(root, name)


def relative(path):
    return os.path.relpath(path, PROJECT_DIR).replace(os.sep, "/")


@pytest.mark.parametrize("path", sorted(
    list(project_files("tasktracker", ".py")) + list(project_files("tests", ".py"))
), ids=relative)
def test_python_files_start_with_course_header(path):
    with open(path, encoding="utf-8") as f:
        assert f.read().startswith(HEADER)


@pytest.mark.parametrize("path", sorted(
    path for path in project_files("tasktracker/templates", ".html")
    if os.path.basename(path) != "base.html"
), ids=relative)
def test_every_template_extends_base(path):
    with open(path, encoding="utf-8") as f:
        assert f.read().startswith("{% extends 'base.html' %}")


def test_requirements_txt_is_plain_text_with_dependencies():
    with open(os.path.join(PROJECT_DIR, "requirements.txt"), "rb") as f:
        data = f.read()

    # UTF-16 (what "pip freeze > requirements.txt" makes in Windows PowerShell 5.1)
    # starts with a byte-order mark; Git and GitHub then treat the file as binary
    assert not data.startswith((b"\xff\xfe", b"\xfe\xff")), "requirements.txt is UTF-16, not UTF-8"

    packages = {
        re.split(r"[=<>~!\[;\s]", line, maxsplit=1)[0].lower()
        for line in data.decode("utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }
    assert {"flask", "werkzeug", "pytest"} <= packages


def test_gitignore_keeps_database_and_secrets_out_of_git():
    with open(os.path.join(PROJECT_DIR, ".gitignore"), encoding="utf-8") as f:
        patterns = {line.strip() for line in f}
    assert {"instance/", ".env", ".venv/", "__pycache__/", ".pytest_cache/"} <= patterns


def test_tests_use_a_temporary_database(app, tmp_path):
    database = os.path.abspath(app.config["DATABASE"])
    assert os.path.commonpath([database, str(tmp_path)]) == str(tmp_path)
    assert database != os.path.join(PROJECT_DIR, "instance", "tasktracker.sqlite")
