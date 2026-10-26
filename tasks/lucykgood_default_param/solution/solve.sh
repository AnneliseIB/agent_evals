#!/bin/bash
set -euo pipefail

cat > /app/greeting.py <<'PYTHON'
def greet(name="World"):
    return f"Hello, {name}!"
PYTHON
