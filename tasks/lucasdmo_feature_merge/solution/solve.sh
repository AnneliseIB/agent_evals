#!/bin/bash
set -euo pipefail

cd /app
git switch -c feature/subtract
cat >> calculator.py <<'PY'


def subtract(a, b):
    return a - b
PY
git add calculator.py
git commit -m "Add subtract function"
git switch main
git merge --no-ff feature/subtract -m "Merge feature/subtract"
