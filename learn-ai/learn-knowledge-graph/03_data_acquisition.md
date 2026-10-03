# 第3课：数据接入 — 多源异构数据采集

> 前置：第 2 课（Schema 已定）  
> 关联：[`06_construction_pipeline.md`](06_construction_pipeline.md) 流水线编排

数据源决定图谱上限。本课讲**结构化、半结构化、非结构化**三类数据的接入模式与工程实践。

---

## 1. 数据源分类

```
┌─────────────────────────────────────────────────────────┐
│                    知识图谱数据源                          │
├──────────────┬──────────────────┬───────────────────────┤
│ 结构化        │ 半结构化          │ 非结构化               │
│ PostgreSQL   │ JSON / CSV       │ PDF / Word / HTML     │
│ MySQL        │ API 响应          │ 邮件 / 聊天记录         │
│ Excel        │ 日志 (JSON Lines) │ 扫描件 OCR             │
├──────────────┴──────────────────┴───────────────────────┤
│ 接入难度：低 ──────────────────────────────→ 高          │
│ 抽取成本：低 ──────────────────────────────→ 高          │
└─────────────────────────────────────────────────────────┘
```

| 类型 | 典型来源 | 接入方式 | 图谱构建路径 |
|------|----------|----------|-------------|
| 结构化 | HR 系统、CRM | SQL 同步 / CDC | 字段映射 → 直接写图 |
| 半结构化 | 开放 API、导出 JSON | ETL 解析 | 规则映射 + 少量 NLP |
| 非结构化 | 制度文档、Wiki | 文档解析 + NLP/LLM | 实体关系抽取（第 4 课） |

---

## 2. 结构化数据：SQL → 图谱

### 2.1 表到图的映射规则

```
关系型表                    图谱映射
─────────────────────────────────────────
employees 表               → Person 节点
departments 表             → Department 节点
employee_dept 关联表       → MEMBER_OF 关系
projects + assignments     → Project 节点 + WORKS_ON 关系
```

### 2.2 Python 批量同步示例

```python
import psycopg2
from neo4j import GraphDatabase

def sync_employees(pg_conn, neo4j_driver):
    with pg_conn.cursor() as cur:
        cur.execute("""
            SELECT e.id, e.name, e.email, d.id AS dept_id, d.name AS dept_name
            FROM employees e
            JOIN employee_dept ed ON e.id = ed.employee_id
            JOIN departments d ON ed.dept_id = d.id
            WHERE e.updated_at > %s
        """, (last_sync_time,))

        rows = cur.fetchall()

    cypher = """
    UNWIND $rows AS row
    MERGE (p:Person {id: row.id})
    SET p.name = row.name, p.email = row.email,
        p.source = 'hr_db', p.updated_at = datetime()
    MERGE (d:Department {id: row.dept_id})
    SET d.name = row.dept_name
    MERGE (p)-[:MEMBER_OF]->(d)
    """
    with neo4j_driver.session() as session:
        session.run(cypher, rows=[dict(r) for r in rows])
```

**关键：** 用 `MERGE` 保证幂等——重复跑同步不会产生重复节点。

### 2.3 CDC（变更数据捕获）

| 方案 | 工具 | 适用 |
|------|------|------|
| 定时全量/增量 | Airflow + SQL | 数据量中小、延迟可接受 |
| Binlog CDC | Debezium → Kafka | 实时性要求高 |
| 触发器 / updated_at | 应用层轮询 | 简单场景 |

---

## 3. 半结构化数据：API 与文件

### 3.1 REST API 接入

```python
import httpx

def fetch_and_normalize(base_url: str, token: str) -> list[dict]:
    resp = httpx.get(
        f"{base_url}/api/v1/projects",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    resp.raise_for_status()
    raw = resp.json()["data"]

    return [
        {
            "id": f"proj_{item['id']}",
            "name": item["name"],
            "owner_id": f"person_{item['owner']['id']}",
            "status": item.get("status", "active"),
            "source": "project_api",
        }
        for item in raw
    ]
```

### 3.2 CSV / JSON Lines

```python
import json

def load_jsonl(path: str):
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)
```

**规范：** 所有接入数据统一转为 **Canonical Record**（中间格式），再写图：

```python
@dataclass
class CanonicalNode:
    label: str
    id: str
    properties: dict

@dataclass
class CanonicalEdge:
    type: str
    from_id: str
    to_id: str
    properties: dict = field(default_factory=dict)
```

---

## 4. 非结构化数据：文档解析

### 4.1 文档处理流水线

```
原始文件 (PDF/DOCX/HTML)
    ↓
格式解析 (PyMuPDF / python-docx / BeautifulSoup)
    ↓
文本分块 (Chunk，保留标题层级)
    ↓
元数据提取 (作者、日期、部门)
    ↓
实体关系抽取（第 4 课）
    ↓
写入 Staging 层 → 质量审核 → 正式图谱
```

### 4.2 分块策略

| 策略 | 说明 | 适用 |
|------|------|------|
| 固定长度 | 512/1024 token + overlap | 通用 RAG |
| 结构感知 | 按标题/段落/表格 | 制度文档、Wiki |
| 语义分块 | Embedding 相似度切分 | 长报告 |

```python
def chunk_by_heading(text: str, max_chars: int = 2000) -> list[str]:
    sections = re.split(r"\n(?=#{1,3}\s)", text)
    chunks, buf = [], ""
    for sec in sections:
        if len(buf) + len(sec) > max_chars and buf:
            chunks.append(buf.strip())
            buf = sec
        else:
            buf += "\n" + sec
    if buf.strip():
        chunks.append(buf.strip())
    return chunks
```

---

## 5. 数据源注册表（团队规范）

维护 `docs/data-sources.md`：

```markdown
| 数据源 ID | 类型 | 负责人 | 同步频率 | 目标 Label/Relation | SLA |
|-----------|------|--------|----------|---------------------|-----|
| hr_db     | PostgreSQL | 张三 | 每日 02:00 | Person, Department, MEMBER_OF | T+1 |
| project_api | REST | 李四 | 每小时 | Project, WORKS_ON | 1h |
| wiki_docs | Confluence | 王五 | 每周 | Document, MENTIONS | 7d |
```

---

## 6. 接入层安全与合规

| 要求 | 实践 |
|------|------|
| 凭证管理 | 环境变量 / Vault，禁止硬编码 |
| 最小权限 | DB 只读账号、API scoped token |
| PII 脱敏 | 手机号、身份证 hash 或掩码后再入图 |
| 审计日志 | 记录每次同步的数据量、耗时、错误 |
| 数据留存 | 原始文档与图谱版本对应，支持回溯 |

---

## 7. Staging 层设计

```
数据源 → Staging Graph（待审核）→ Production Graph（正式）
              │
              ├─ 低置信度实体
              ├─ 冲突待消解
              └─ 人工复核队列
```

Staging 节点额外 Label：`:Staging` 或独立 Neo4j 数据库（dev/staging/prod 三库隔离，见第 10 课）。

---

## 8. 动手练习

1. 编写 CSV → CanonicalNode/Edge 转换器（用 `practice/data/sample_employees.csv`）
2. 设计你项目的「数据源注册表」3 行
3. 用 `MERGE` 写 Cypher，验证同一 id 重复导入不会 duplicate
4. 思考：Wiki 文档应按 Document 节点存储，还是只抽取实体不写 Document 节点？

---

## 9. 自检清单

- [ ] 能区分三类数据源的接入策略
- [ ] 理解 SQL 表到图节点的映射规则
- [ ] 会使用 Canonical Record 中间格式
- [ ] 知道 Staging 层的作用
- [ ] 了解 PII 与凭证管理基本要求

---

## 下一课

[`04_entity_relation_extraction.md`](04_entity_relation_extraction.md) — 实体关系抽取
