"""
Use this file to define pytest tests that verify the outputs of the task.

This file will be copied to /tests/test_outputs.py and run by the /tests/test.sh file
from the working directory.
"""

from pathlib import Path

APP = Path("/app")
OUTPUT = APP / "new_file.md"

def test_output_is_regular_file():
    """Test that the file was created."""
    assert OUTPUT.exists()
    assert OUTPUT.is_file()
    assert not OUTPUT.is_symlink()

def test_output_is_empty():
    """Test that the output file is empty."""
    assert OUTPUT.read_bytes() == b""

def test_only_requested_file_exists():
    """Test no other files were created."""
    entries = {
        path.relative_to(APP).as_posix()
        for path in APP.rglob("*")
    }
    assert entries == {"new_file.md"}