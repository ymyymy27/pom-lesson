"""Todo API — 第 6/7 课集成测试示例"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Todo API")

todos: list[dict] = []
_next_id = 1


class TodoCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    done: bool = False


class TodoUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None


class TodoResponse(BaseModel):
    id: int
    title: str
    done: bool


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/todos", status_code=201, response_model=TodoResponse)
def create_todo(todo: TodoCreate):
    global _next_id
    item = {"id": _next_id, "title": todo.title, "done": todo.done}
    _next_id += 1
    todos.append(item)
    return item


@app.get("/todos", response_model=list[TodoResponse])
def list_todos():
    return todos


@app.get("/todos/{todo_id}", response_model=TodoResponse)
def get_todo(todo_id: int):
    for item in todos:
        if item["id"] == todo_id:
            return item
    raise HTTPException(status_code=404, detail="Todo not found")


@app.patch("/todos/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, update: TodoUpdate):
    for item in todos:
        if item["id"] == todo_id:
            if update.title is not None:
                item["title"] = update.title
            if update.done is not None:
                item["done"] = update.done
            return item
    raise HTTPException(status_code=404, detail="Todo not found")


@app.delete("/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int):
    for i, item in enumerate(todos):
        if item["id"] == todo_id:
            todos.pop(i)
            return
    raise HTTPException(status_code=404, detail="Todo not found")
