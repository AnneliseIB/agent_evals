"""Pytest checks for the duplicated file inside the task sandbox."""

from pathlib import Path

import pytest

GREET = 'def greet(name):\n    return f"Hello, {name}!"\n'
GREET2 = 'def greet(name):\n    return f"Hi, {name}!"\n'


@pytest.fixture
def scripts():
    return Path("/app/scripts")


@pytest.mark.parametrize(("name", "content"), [("greet.py", GREET), ("greet2.py", GREET2)])
def test_existing_file_unchanged(scripts, name, content):
    assert (scripts / name).read_text() == content


def test_copy_is_exact_duplicate(scripts):
    copy = scripts / "greet3.py"
    assert copy.is_file()
    assert not copy.is_symlink()
    assert copy.read_bytes() == (scripts / "greet.py").read_bytes()


def test_no_other_files(scripts):
    names = {path.name for path in scripts.iterdir() if path.is_file()}
    assert names == {"greet.py", "greet2.py", "greet3.py"}
