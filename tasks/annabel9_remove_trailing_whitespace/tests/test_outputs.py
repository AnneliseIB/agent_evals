
"""Pytest checks for removing trailing whitespace."""
import subprocess
from pathlib import Path

FILE = Path("/app/whitespace.py")


def test_no_trailing_whitespace():
    """Test that no lines contain trailing spaces or tabs."""
    lines = FILE.read_text().splitlines()

    for line in lines:
        assert line == line.rstrip(" \t")


def test_code_preserved():
    """Test that the original code is preserved."""
    expected = (
        "def greet(name):\n"
        '    message = "Hello, " + name + "!"\n'
        "    return message\n"
    )

    assert FILE.read_text() == expected


def test_python_runs():
    """Test that the Python code runs without errors."""
    result = subprocess.run(
        ["python3", str(FILE)],
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert result.returncode == 0
