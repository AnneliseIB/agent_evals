"""Check that cleanup removes generated files while preserving the workspace."""

import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.fixture(params=["project", "project with spaces"])
def cleanup_workspace(tmp_path: Path, request: pytest.FixtureRequest) -> Path:
    project = tmp_path / request.param
    project.mkdir()
    shutil.copyfile(Path(__file__).resolve().parents[1] / "Makefile", project / "Makefile")
    return project


def test_clean_removes_generated_outputs_and_preserves_project(cleanup_workspace: Path) -> None:
    generated = [
        "jobs/trial/result.json",
        ".harbor/state.json",
        ".pytest_cache/v/cache/nodeids",
        "nested/.pytest_cache/v/cache/nodeids",
        ".ruff_cache/cache",
        "nested/.ruff_cache/cache",
        "src/coding_agent/__pycache__/agent.cpython-312.pyc",
        "nested directory/__pycache__/helper.cpython-312.pyc",
        ".coverage",
        ".coverage.worker",
        "htmlcov/index.html",
        "build/lib/coding_agent/agent.py",
        "dist/coding_agent.whl",
        "src/coding_agent.egg-info/PKG-INFO",
    ]
    preserved = [
        ".env",
        "uv.lock",
        ".python-version",
        "README.md",
        "src/coding_agent/agent.py",
        "tasks/example/instruction.md",
        ".git/config",
        ".git/hooks/__pycache__/hook.pyc",
        ".venv/bin/python",
        ".venv/lib/__pycache__/module.pyc",
        ".venv/lib/.pytest_cache/data",
        ".venv/lib/package.egg-info/PKG-INFO",
        "nested/.venv/lib/__pycache__/module.pyc",
    ]
    for name in generated + preserved:
        target = cleanup_workspace / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"original contents of {name}\n")

    for _ in range(2):
        subprocess.run(["make", "clean"], cwd=cleanup_workspace, check=True, capture_output=True)

        for name in generated:
            assert not (cleanup_workspace / name).exists(), name
        for name in preserved:
            assert (cleanup_workspace / name).read_text() == f"original contents of {name}\n"
        assert (cleanup_workspace / "Makefile").is_file()
