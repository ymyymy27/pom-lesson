"""CSV → Neo4j 最小流水线（幂等 MERGE）。运行：python pipeline_demo.py"""

import csv
import os
from pathlib import Path

from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_AUTH = (
    os.getenv("NEO4J_USER", "neo4j"),
    os.getenv("NEO4J_PASSWORD", "changeme"),
)
CSV_PATH = Path(__file__).parent / "data" / "sample_employees.csv"


def extract_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def transform(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    nodes: list[dict] = []
    edges: list[dict] = []
    seen_nodes: set[str] = set()

    for row in rows:
        pid = f"person_{row['employee_id']}"
        did = f"dept_{row['dept_id']}"

        if pid not in seen_nodes:
            nodes.append({
                "label": "Person",
                "id": pid,
                "props": {
                    "name": row["name"],
                    "email": row["email"],
                    "title": row.get("title", ""),
                    "source": "csv",
                    "status": "active",
                },
            })
            seen_nodes.add(pid)

        if did not in seen_nodes:
            nodes.append({
                "label": "Department",
                "id": did,
                "props": {"name": row["dept_name"], "source": "csv"},
            })
            seen_nodes.add(did)

        edges.append({"type": "MEMBER_OF", "from_id": pid, "to_id": did})

    return nodes, edges


def load(driver, nodes: list[dict], edges: list[dict]) -> None:
    with driver.session() as session:
        for label in sorted(set(n["label"] for n in nodes)):
            batch = [{"id": n["id"], "props": n["props"]} for n in nodes if n["label"] == label]
            session.run(
                f"""
                UNWIND $batch AS row
                MERGE (n:{label} {{id: row.id}})
                SET n += row.props, n.updated_at = datetime()
                """,
                batch=batch,
            )

        session.run(
            """
            UNWIND $edges AS e
            MATCH (a {id: e.from_id}), (b {id: e.to_id})
            CALL apoc.merge.relationship(a, e.type, {}, {}, b) YIELD rel
            RETURN count(rel) AS c
            """,
            edges=[{"type": e["type"], "from_id": e["from_id"], "to_id": e["to_id"]} for e in edges],
        )


def load_without_apoc(driver, nodes: list[dict], edges: list[dict]) -> None:
    """APOC 不可用时的 fallback。"""
    with driver.session() as session:
        for label in sorted(set(n["label"] for n in nodes)):
            batch = [{"id": n["id"], "props": n["props"]} for n in nodes if n["label"] == label]
            session.run(
                f"""
                UNWIND $batch AS row
                MERGE (n:{label} {{id: row.id}})
                SET n += row.props, n.updated_at = datetime()
                """,
                batch=batch,
            )
        for e in edges:
            session.run(
                f"""
                MATCH (a {{id: $from_id}}), (b {{id: $to_id}})
                MERGE (a)-[r:{e['type']}]->(b)
                SET r.updated_at = datetime()
                """,
                from_id=e["from_id"],
                to_id=e["to_id"],
            )


def main():
    rows = extract_csv(CSV_PATH)
    nodes, edges = transform(rows)
    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
    try:
        load(driver, nodes, edges)
    except Exception:
        print("APOC unavailable, using fallback MERGE for relationships.")
        load_without_apoc(driver, nodes, edges)
    with driver.session() as session:
        cnt = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        print(f"Pipeline done. Total nodes in graph: {cnt}")
    driver.close()


if __name__ == "__main__":
    main()
