#!/bin/bash
set -euo pipefail

cat > /app/calculator.py <<'PY'
def add(a, b):
    return a + b
PY
