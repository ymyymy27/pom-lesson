"""写入演示组织知识图谱。运行：python seed_demo_graph.py"""

import os
from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_AUTH = (
    os.getenv("NEO4J_USER", "neo4j"),
    os.getenv("NEO4J_PASSWORD", "changeme"),
)
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")


def seed(tx):
    tx.run("MATCH (n) DETACH DELETE n")

    tx.run("""
        CREATE (co:Company {id: 'co_001', name: '示例科技有限公司', source: 'seed'})
        CREATE (d1:Department {id: 'dept_d01', name: '研发一部', source: 'seed'})
        CREATE (d2:Department {id: 'dept_d02', name: '产品部', source: 'seed'})
        CREATE (p1:Person {id: 'person_001', name: '张三', email: 'zhangsan@example.com',
                            title: '高级工程师', status: 'active', source: 'seed'})
        CREATE (p2:Person {id: 'person_002', name: '李四', email: 'lisi@example.com',
                            title: '技术负责人', status: 'active', source: 'seed'})
        CREATE (p3:Person {id: 'person_003', name: '王五', email: 'wangwu@example.com',
                            title: '产品经理', status: 'active', source: 'seed'})
        CREATE (proj:Project {id: 'proj_order', name: '订单系统', status: 'active', source: 'seed'})
        CREATE (d1)-[:BELONGS_TO]->(co)
        CREATE (d2)-[:BELONGS_TO]->(co)
        CREATE (p1)-[:MEMBER_OF]->(d1)
        CREATE (p2)-[:MEMBER_OF]->(d1)
        CREATE (p3)-[:MEMBER_OF]->(d2)
        CREATE (p1)-[:REPORTS_TO]->(p2)
        CREATE (p1)-[:WORKS_ON {role: '后端'}]->(proj)
        CREATE (p2)-[:WORKS_ON {role: '负责人'}]->(proj)
        CREATE (proj)-[:OWNED_BY]->(p2)
    """)

    tx.run("""
        CREATE CONSTRAINT person_id IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE
    """)
    tx.run("""
        CREATE CONSTRAINT company_id IF NOT EXISTS FOR (c:Company) REQUIRE c.id IS UNIQUE
    """)
    tx.run("""
        CREATE INDEX person_name IF NOT EXISTS FOR (p:Person) ON (p.name)
    """)


def main():
    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
    with driver.session(database=NEO4J_DATABASE) as session:
        session.execute_write(seed)
        count = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        print(f"Demo graph seeded to database '{NEO4J_DATABASE}'. Total nodes: {count}")
    driver.close()


if __name__ == "__main__":
    main()
