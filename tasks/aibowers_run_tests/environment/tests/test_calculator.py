import pytest

from calculator import add, divide


def test_add_positive_numbers():
    assert add(2, 3) == 5


def test_divide_returns_quotient():
    assert divide(10, 2) == 5



def test_divide_with_zero_returns_zero():
    assert divide(5, 0) == 0


@pytest.mark.skip(reason="demonstrates a skipped test")
def test_decimal_division():
    assert divide(1, 4) == 0.25
