#!/bin/bash
set -euo pipefail

# Prepend the docstring so the rest of the file stays byte-for-byte identical.
docstring=$(mktemp)
cat > "$docstring" <<'PY'
"""Small helpers for turning free-form text into slugs, previews, and counts.

Example:

    >>> from textutils import slugify, truncate, word_count
    >>> slugify("Hello, World!")
    'hello-world'
    >>> truncate("The quick brown fox", 12)
    'The quick...'
    >>> word_count("one two three")
    3
"""

PY
cat "$docstring" /app/textutils.py > /app/textutils.py.new
mv /app/textutils.py.new /app/textutils.py
rm "$docstring"
