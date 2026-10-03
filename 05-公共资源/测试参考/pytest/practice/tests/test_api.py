import pytest
from fastapi.testclient import TestClient
from app import main as app_module
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_todos():
    app_module.todos.clear()
    app_module._next_id = 1
    yield
    app_module.todos.clear()
    app_module._next_id = 1


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.integration
def test_create_and_list_todos(client):
    create = client.post("/todos", json={"title": "学习 pytest", "done": False})
    assert create.status_code == 201
    assert create.json()["title"] == "学习 pytest"

    response = client.get("/todos")
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.integration
def test_mark_todo_done(client):
    create = client.post("/todos", json={"title": "任务", "done": False})
    todo_id = create.json()["id"]
    response = client.patch(f"/todos/{todo_id}", json={"done": True})
    assert response.status_code == 200
    assert response.json()["done"] is True


@pytest.mark.integration
def test_get_todo_not_found(client):
    response = client.get("/todos/999")
    assert response.status_code == 404


@pytest.mark.integration
def test_delete_todo(client):
    create = client.post("/todos", json={"title": "待删除", "done": False})
    todo_id = create.json()["id"]
    delete = client.delete(f"/todos/{todo_id}")
    assert delete.status_code == 204
    assert client.get("/todos").json() == []
