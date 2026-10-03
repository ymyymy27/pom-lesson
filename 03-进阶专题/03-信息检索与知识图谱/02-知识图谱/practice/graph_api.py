"""Graph API 示例。运行：uvicorn graph_api:app --reload --app-dir practice"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from neo4j import GraphDatabase
from pydantic import BaseModel

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_AUTH = (
    os.getenv("NEO4J_USER", "neo4j"),
    os.getenv("NEO4J_PASSWORD", "changeme"),
)

driver = None


class GraphRepository:
    def __init__(self, neo4j_driver):
        self._driver = neo4j_driver

    def get_person_with_projects(self, person_id: str) -> dict | None:
        query = """
        MATCH (p:Person {id: $id})
        OPTIONAL MATCH (p)-[w:WORKS_ON]->(proj:Project)
        OPTIONAL MATCH (p)-[:MEMBER_OF]->(d:Department)
        RETURN p {.*,
            department: d {.id, .name},
            projects: collect(DISTINCT proj {.id, .name, .status, role: w.role})
        } AS person
        """
        with self._driver.session() as session:
            record = session.run(query, id=person_id).single()
            return record["person"] if record else None

    def search_people(self, name: str, limit: int = 20) -> list[dict]:
        query = """
        MATCH (p:Person)
        WHERE p.name CONTAINS $name
          AND coalesce(p.status, 'active') = 'active'
        RETURN p {.id, .name, .email, .title} AS person
        ORDER BY p.name
        LIMIT $limit
        """
        with self._driver.session() as session:
            return [r["person"] for r in session.run(query, name=name, limit=limit)]

    def get_neighbors(self, entity_id: str, limit: int = 30) -> dict:
        query = """
        MATCH (start {id: $id})-[r]-(neighbor)
        RETURN start {.id, .name} AS center,
               collect(DISTINCT neighbor {.id, .name})[..$limit] AS neighbors,
               collect(DISTINCT type(r)) AS relation_types
        """
        with self._driver.session() as session:
            record = session.run(query, id=entity_id, limit=limit).single()
            return dict(record) if record else {}


repo: GraphRepository | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global driver, repo
    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
    repo = GraphRepository(driver)
    yield
    driver.close()


app = FastAPI(title="Org Knowledge Graph API", lifespan=lifespan)


class PersonResponse(BaseModel):
    id: str
    name: str
    email: str | None = None
    title: str | None = None
    department: dict | None = None
    projects: list[dict] = []


@app.get("/health")
def health():
    try:
        with driver.session() as session:
            session.run("RETURN 1").single()
        return {"status": "ok", "neo4j": "connected"}
    except Exception as exc:
        return {"status": "degraded", "error": str(exc)}


@app.get("/v1/persons/{person_id}", response_model=PersonResponse)
def get_person(person_id: str):
    data = repo.get_person_with_projects(person_id)
    if not data:
        raise HTTPException(status_code=404, detail="Person not found")
    return data


@app.get("/v1/persons/search")
def search_persons(q: str = Query(min_length=1), limit: int = Query(default=20, le=100)):
    return {"results": repo.search_people(q, limit=limit)}


@app.get("/v1/neighbors/{entity_id}")
def neighbors(entity_id: str, limit: int = Query(default=30, le=100)):
    data = repo.get_neighbors(entity_id, limit=limit)
    if not data:
        raise HTTPException(status_code=404, detail="Entity not found")
    return data
