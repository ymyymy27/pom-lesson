import pytest
from unittest.mock import Mock
from user_service import User, UserNotFoundError, UserService


@pytest.fixture
def mock_repo():
    return Mock()


@pytest.fixture
def service(mock_repo):
    return UserService(repo=mock_repo)


def test_get_user_success(service, mock_repo, sample_user):
    mock_repo.find_by_id.return_value = sample_user
    user = service.get(1)
    assert user.name == "Alice"
    mock_repo.find_by_id.assert_called_once_with(1)


def test_get_user_not_found(service, mock_repo):
    mock_repo.find_by_id.return_value = None
    with pytest.raises(UserNotFoundError, match="User 999 not found"):
        service.get(999)


def test_create_user(service, mock_repo):
    saved = User(id=1, name="Bob", email="bob@test.com")
    mock_repo.save.return_value = saved
    user = service.create("Bob", "bob@test.com")
    assert user.name == "Bob"
    mock_repo.save.assert_called_once()
