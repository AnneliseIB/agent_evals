#!/bin/bash
set -u

cd /app

output_file=$(mktemp)
pytest_status=0
python -m pytest -q -rA -p no:cacheprovider >"$output_file" 2>&1 || pytest_status=$?

awk '/^FAILED / { print $2 }' "$output_file" > /app/failing_tests.txt
rm -f "$output_file"

# A failing test run is an expected task outcome, not a solution-script error.
exit 0