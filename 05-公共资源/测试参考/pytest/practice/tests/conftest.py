import pytest
from user_service import User, UserService


@pytest.fixture
def sample_user():
    return User(id=1, name="Alice", email="a@b.com")
