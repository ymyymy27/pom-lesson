import pytest
from validators import is_valid_email, is_valid_password


@pytest.mark.parametrize(
    "email,expected",
    [
        ("a@b.com", True),
        ("user+tag@example.org", True),
        ("invalid", False),
        ("", False),
        ("missing-at.com", False),
    ],
)
def test_email_validation(email, expected):
    assert is_valid_email(email) == expected


@pytest.mark.parametrize(
    "password,valid",
    [
        ("Abcdef12", True),
        ("short1A", False),
        ("nouppercase1", False),
        ("NOLOWERCASE1", False),
        ("NoDigitsHere", False),
        ("", False),
    ],
)
def test_password(password, valid):
    assert is_valid_password(password) == valid
