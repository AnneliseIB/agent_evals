#!/bin/bash
set -euo pipefail

cat > /app/modified_files.py <<'PYTHON'
"""Find files with staged or unstaged Git changes."""

import os
import subprocess


def list_modified_files(repo_path):
    """Return sorted, unique repository-relative paths with changes."""
    paths = set()
    for options in ([], ["--cached"]):
        result = subprocess.run(
            ["git", "-C", str(repo_path), "diff", *options,
             "--name-only", "--no-renames", "-z", "--"],
            check=True, capture_output=True,
        )
        paths.update(os.fsdecode(path) for path in result.stdout.split(b"\0") if path)
    return sorted(paths)
PYTHON
