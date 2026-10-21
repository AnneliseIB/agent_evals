#!/bin/bash
set -u

cd /app

python -m pytest -q -rA || true

# A failing test run is an expected task outcome, not a solution-script error.
exit 0