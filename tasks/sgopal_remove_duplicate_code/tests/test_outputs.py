"""Pytest checks for the duplicate removal inside the task sandbox."""

import functions


def test_one_duplicate_function_removed():
    assert not (hasattr(functions, "function_a") and hasattr(functions, "function_b"))
