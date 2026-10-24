"""Pytest checks for the duplicate removal inside the task sandbox."""

import functions
from functions import function_a, function_b

def test_function_b_removed():
    assert not hasattr(functions, "function_b")


def test_function_a_unchanged():
    assert functions.function_a() == "hello"
