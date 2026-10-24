"""Pytest checks for the calculator inside the task sandbox."""

import pytest
from calculator import add


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        (2, 3, 5),
        (-2, 3, 1),
        (-2, -3, -5),
        (0, 0, 0),
        (5, 0, 5),
        (1.5, 2.25, 3.75),
    ],
)
def test_add(a, b, expected):
    assert add(a, b) == expected
