"""Check Git's ignore behavior inside the sandbox."""

import subprocess
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    ("path", "ignored"),
    [(".env", True), ("config/.env", True), ("app.log", True), ("main.py", False)],
)
def test_ignore_rules(path, ignored):
    assert Path("/app/.gitignore").is_file()
    result = subprocess.run(
        ["git", "check-ignore", "--no-index", "-q", path], cwd="/app", check=False
    )
    assert result.returncode == (0 if ignored else 1)
