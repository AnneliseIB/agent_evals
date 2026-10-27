"""Basic v0 checks for listing modified Git files."""

import importlib.util
import subprocess
from pathlib import Path

import pytest


def list_modified_files(repo_path):
    """Load the sandbox submission, or the starter when running locally."""
    source = Path("/app/modified_files.py")
    if not source.is_file():
        source = Path(__file__).resolve().parents[1] / "environment" / "modified_files.py"
    spec = importlib.util.spec_from_file_location("modified_files", source)
    assert spec is not None and spec.loader is not None, f"Cannot load {source}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.list_modified_files(repo_path)


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path):
    """Create a clean repository with two tracked files for each test."""
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "eval@example.invalid")
    git(tmp_path, "config", "user.name", "Eval")
    for name in ["alpha.txt", "zeta.txt"]:
        (tmp_path / name).write_text("original\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "Initial files")
    return tmp_path


def test_clean_repository(repo):
    assert list_modified_files(str(repo)) == []


@pytest.mark.parametrize("staged", [False, True])
def test_modified_file(repo, staged):
    (repo / "alpha.txt").write_text("changed\n")
    if staged:
        git(repo, "add", "alpha.txt")
    assert list_modified_files(str(repo)) == ["alpha.txt"]


def test_sorted_unique_files(repo):
    (repo / "zeta.txt").write_text("staged\n")
    git(repo, "add", "zeta.txt")
    (repo / "zeta.txt").write_text("unstaged too\n")
    (repo / "alpha.txt").write_text("changed\n")
    assert list_modified_files(str(repo)) == ["alpha.txt", "zeta.txt"]


def test_excludes_untracked_files(repo):
    (repo / "new.txt").write_text("untracked\n")
    assert list_modified_files(str(repo)) == []
