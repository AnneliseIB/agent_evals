"""
Use this file to define pytest tests that verify the outputs of the task.

This file will be copied to /tests/test_outputs.py and run by the /tests/test.sh file
from the working directory.
"""

from pathlib import Path


def test_requirements():
    """Test that numpy was added and pytest was not changed in requirements.txt."""
    requirements = Path("/app/requirements.txt").read_text().splitlines()

    assert requirements[0] == "pytest==9.1.1"
    assert requirements[1] == "numpy==2.5.4"
