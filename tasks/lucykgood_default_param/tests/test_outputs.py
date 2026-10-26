"""Check the default argument and explicit names."""

import inspect

import pytest
from greeting import greet


def test_default_name():
    assert inspect.signature(greet).parameters["name"].default == "World"
    assert greet() == "Hello, World!"


@pytest.mark.parametrize("name", ["Lucy", "Sam", ""])
def test_explicit_name(name):
    assert greet(name) == f"Hello, {name}!"
