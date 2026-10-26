#!/bin/bash
set -euo pipefail

cat > /app/whitespace.py <<'PY'
def greet(name):
    message = "Hello, " + name + "!"
    return message
PY
