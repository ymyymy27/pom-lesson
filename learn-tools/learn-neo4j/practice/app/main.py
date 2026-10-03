"""FastAPI + Neo4j 组织图谱 API。"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from graph_repo import GraphRepo, NEO4J_DATABASE, NEO4J_PASSWORD, NEO4J_URI, NEO4J_USER

repo: GraphRepo | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global repo
    repo = GraphRepo(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE)
    yield
    repo.close()


app = FastAPI(title="Learn Neo4j Org API", lifespan=lifespan)


@app.get("/health")
def health():
    try:
        assert repo is not None
        repo.ping()
        with repo.session() as session:
            count = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        return {"status": "ok", "database": NEO4J_DATABASE, "node_count": count}
    except Exception as e:
        raise HTTPException(503, f"Neo4j unavailable: {e}") from e


@app.get("/persons/{person_id}")
def get_person(person_id: str):
    assert repo is not None
    person = repo.get_person(person_id)
    if not person:
        raise HTTPException(404, "Person not found")
    return person


@app.get("/persons/{person_id}/projects")
def person_projects(person_id: str):
    assert repo is not None
    if not repo.get_person(person_id):
        raise HTTPException(404, "Person not found")
    return repo.list_person_projects(person_id)


@app.get("/departments/{dept_id}/members")
def department_members(dept_id: str):
    assert repo is not None
    members = repo.list_department_members(dept_id)
    if not members:
        raise HTTPException(404, "Department not found or empty")
    return members


@app.get("/org/subgraph")
def org_subgraph(person_id: str, depth: int = 2):
    if depth < 1 or depth > 4:
        raise HTTPException(400, "depth must be between 1 and 4")
    assert repo is not None
    if not repo.get_person(person_id):
        raise HTTPException(404, "Person not found")
    return repo.get_subgraph(person_id, depth)
