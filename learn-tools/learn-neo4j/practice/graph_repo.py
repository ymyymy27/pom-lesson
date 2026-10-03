"""Neo4j Repository 封装 — 供 FastAPI 与 CLI 使用。"""

import os
from contextlib import contextmanager

from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "changeme")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")


class GraphRepo:
    def __init__(
        self,
        uri: str = NEO4J_URI,
        user: str = NEO4J_USER,
        password: str = NEO4J_PASSWORD,
        database: str = NEO4J_DATABASE,
    ):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))
        self._database = database

    def close(self):
        self._driver.close()

    def ping(self) -> bool:
        self._driver.verify_connectivity()
        return True

    @contextmanager
    def session(self):
        with self._driver.session(database=self._database) as session:
            yield session

    def get_person(self, person_id: str) -> dict | None:
        query = "MATCH (p:Person {id: $id}) RETURN p"
        with self.session() as session:
            record = session.run(query, id=person_id).single()
            return dict(record["p"]) if record else None

    def list_person_projects(self, person_id: str) -> list[dict]:
        query = """
        MATCH (p:Person {id: $id})-[r:WORKS_ON]->(proj:Project)
        RETURN proj.id AS id, proj.name AS name, proj.status AS status, r.role AS role
        ORDER BY proj.name
        """
        with self.session() as session:
            return [dict(r) for r in session.run(query, id=person_id)]

    def list_department_members(self, dept_id: str) -> list[dict]:
        query = """
        MATCH (d:Department {id: $dept_id})<-[:MEMBER_OF]-(p:Person)
        RETURN p.id AS id, p.name AS name, p.title AS title, p.email AS email
        ORDER BY p.name
        """
        with self.session() as session:
            return [dict(r) for r in session.run(query, dept_id=dept_id)]

    def get_subgraph(self, person_id: str, depth: int = 2) -> dict:
        # 可变长度路径的上限必须是字面量，depth 由 API 校验为 1–4
        node_query = f"""
        MATCH (center:Person {{id: $id}})
        OPTIONAL MATCH (center)-[*1..{depth}]-(n)
        WITH center, collect(DISTINCT n) AS others
        RETURN center, others
        """
        edge_query = f"""
        MATCH (center:Person {{id: $id}})-[r*1..{depth}]-(n)
        UNWIND r AS rel
        RETURN DISTINCT startNode(rel).id AS source, endNode(rel).id AS target,
               type(rel) AS type, properties(rel) AS properties
        """
        with self.session() as session:
            record = session.run(node_query, id=person_id).single()
            if not record:
                return {"nodes": [], "edges": []}

            def serialize_node(node):
                return {
                    "labels": list(node.labels),
                    **dict(node),
                }

            nodes = [serialize_node(record["center"])]
            for n in record["others"]:
                if n is not None:
                    nodes.append(serialize_node(n))

            edges = [dict(r) for r in session.run(edge_query, id=person_id)]
            return {"nodes": nodes, "edges": edges}


def main():
    repo = GraphRepo()
    try:
        repo.ping()
        person = repo.get_person("person_001")
        print("Person:", person)
        print("Projects:", repo.list_person_projects("person_001"))
        print("Dept members:", repo.list_department_members("dept_d01"))
    finally:
        repo.close()


if __name__ == "__main__":
    main()
