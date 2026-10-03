import pytest
from calculator import add, divide, multiply, subtract


def test_add():
    assert add(2, 3) == 5


def test_add_negative():
    assert add(-1, -2) == -3


def test_subtract():
    assert subtract(10, 3) == 7


def test_multiply():
    assert multiply(3, 4) == 12
    assert multiply(0, 100) == 0


def test_divide():
    assert divide(10, 2) == 5


def test_divide_by_zero():
    with pytest.raises(ValueError, match="除数不能为零"):
        divide(10, 0)


def test_divide_float():
    assert divide(1, 3) == pytest.approx(0.333, rel=1e-2)
