"""
Use this file to define pytest tests that verify the outputs of the task.

This file will be copied to /tests/test_outputs.py and run by the /tests/test.sh file
from the working directory.
"""

from pathlib import Path


def test_file_exists():
    """Test that file was created."""
    file_path = Path("/app/new_file.md")
    assert file_path.is_file(), f"File not found: {file_path}"