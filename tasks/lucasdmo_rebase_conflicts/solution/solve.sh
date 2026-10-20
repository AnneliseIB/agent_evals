#!/bin/bash
set -euo pipefail

cd /app
git rebase main || true
cat > calculator.py <<'PY'
def add(a, b):
    return a + b


def subtract(a, b):
    return a - b


def multiply(a, b):
    return a * b


def power(a, b):
    return a ** b
PY
git add calculator.py
GIT_EDITOR=true git rebase --continue
