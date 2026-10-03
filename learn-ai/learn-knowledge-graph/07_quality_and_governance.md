# 第7课：质量治理 — 校验、冲突消解与权限

> 前置：第 4、6 课  
> 关联：[`09_team_collaboration` 思路] 与 `learn-redis/09_team_collaboration.md` 同类治理思维

图谱垃圾进、垃圾出。本课建立**质量门禁、冲突消解、权限审计**体系，让图谱可信赖。

---

## 1. 质量维度框架

```
┌────────────────────────────────────────────────────────┐
│                  知识图谱质量金字塔                      │
├────────────────────────────────────────────────────────┤
│ L4 应用质量  — 问答准确率、召回率、用户满意度           │
│ L3 语义质量  — 关系正确、无矛盾、本体一致               │
│ L2 完整质量  — 覆盖率、时效性、无孤立节点               │
│ L1 语法质量  — Schema 合规、必填字段、类型正确          │
└────────────────────────────────────────────────────────┘
```

流水线中 **L1/L2 自动校验**，L3 抽样 + 人工，L4 对接下游 Eval。

---

## 2. L1 语法质量：Schema 校验

```python
def validate_node(node: dict, schema: dict) -> list[str]:
    errors = []
    label = node["label"]
    spec = schema["nodes"].get(label)
    if not spec:
        return [f"Unknown label: {label}"]

    props = node.get("properties", {})
    for name, rule in spec["properties"].items():
        if rule.get("required") and name not in props:
            errors.append(f"{label}.{name} is required")
        if name in props and rule.get("type") == "enum":
            if props[name] not in rule["values"]:
                errors.append(f"{label}.{name} invalid enum: {props[name]}")
    return errors
```

### CI 集成

```yaml
# .github/workflows/kg-quality.yml
- name: Validate schema
  run: python scripts/validate_schema.py practice/schema/org_kg_schema.yaml
- name: Golden extraction test
  run: pytest tests/test_extraction_golden.py --min-precision 0.85
```

---

## 3. L2 完整质量：图完整性规则

| 规则 | Cypher 检测 | 严重级别 |
|------|-------------|----------|
| 孤立 Person（无关系） | `MATCH (p:Person) WHERE NOT (p)--() RETURN p` | Warning |
| Project 无 OWNER | `MATCH (p:Project) WHERE NOT (p)-[:OWNED_BY]->()` | Error |
| 重复 id | `MATCH (n) WITH n.id AS id, count(*) AS c WHERE c>1 RETURN id` | Critical |
| 过期数据 | `MATCH (n) WHERE n.updated_at < datetime() - duration('P90D')` | Info |

```python
QUALITY_RULES = [
    {
        "name": "duplicate_person_id",
        "severity": "critical",
        "cypher": """
            MATCH (p:Person)
            WITH p.id AS id, count(*) AS cnt WHERE cnt > 1
            RETURN id, cnt
        """,
    },
    {
        "name": "project_without_owner",
        "severity": "error",
        "cypher": """
            MATCH (p:Project {status: 'active'})
            WHERE NOT (p)-[:OWNED_BY]->(:Person)
            RETURN p.id, p.name
        """,
    },
]
```

**Publish 门禁：** Critical/Error > 0 则阻断。

---

## 4. L3 语义质量：冲突消解

### 4.1 属性冲突

```
hr_db:      Person.name = "张三", title = "工程师"
doc_extract: Person.name = "张三", title = "高级工程师"
```

**策略：来源优先级 + 时间戳**

```python
SOURCE_PRIORITY = {"hr_db": 100, "manual": 90, "doc_extract": 50, "llm": 30}

def merge_properties(existing: dict, incoming: dict, incoming_source: str) -> dict:
    merged = dict(existing)
    for key, val in incoming.items():
        if key not in merged:
            merged[key] = val
        elif SOURCE_PRIORITY.get(incoming_source, 0) > SOURCE_PRIORITY.get(existing.get("source", ""), 0):
            merged[key] = val
    return merged
```

### 4.2 关系冲突

```
源 A: 张三 -WORKS_AT-> 阿里巴巴
源 B: 张三 -WORKS_AT-> 腾讯   （跳槽未同步）
```

处理：**时间有效性**（见第 5 课）+ 人工复核队列。

### 4.3 人工复核工作流

```
Staging (status=pending_review)
    → 审核 UI / Neo4j Browser + 清单
    → approved / rejected
    → Publish 或 丢弃
```

---

## 5. 置信度与溯源

每个事实应可追溯：

```cypher
(p:Person {name: '张三'})
  -[:WORKS_ON {
      role: '后端',
      confidence: 0.87,
      source: 'doc_extract',
      source_doc_id: 'wiki-123',
      source_span: '张三负责订单系统后端开发',
      extracted_at: datetime('2026-03-01T10:00:00')
  }]->(proj:Project)
```

| confidence | 动作 |
|------------|------|
| ≥ 0.9 | 自动 Publish |
| 0.7 – 0.9 | Staging + 抽检 |
| < 0.7 | 人工复核必填 |

---

## 6. 权限与审计

### 6.1 访问分层

| 角色 | 读 | 写 Staging | Publish | Schema 变更 |
|------|-----|-----------|---------|------------|
| 开发者 | dev 库 | ✅ | ❌ | PR 评审 |
| 数据工程师 | staging/prod 读 | ✅ | ✅ | 提案 |
| 领域专家 | prod 读 | 复核 | ❌ | 审批 |
| 服务账号 | API 读 | ❌ | ❌ | ❌ |

### 6.2 Neo4j 权限（Enterprise）

社区版依赖**应用层 RBAC** + 网络隔离（prod 仅内网）。

### 6.3 审计日志

```python
def audit_log(action: str, actor: str, target: str, detail: dict):
    # 写入 PostgreSQL / ELK
    logger.info("kg_audit", extra={
        "action": action,      # publish | reject | schema_change
        "actor": actor,
        "target": target,
        "detail": detail,
        "ts": datetime.utcnow().isoformat(),
    })
```

---

## 7. 治理文档模板

`docs/kg-governance.md`：

```markdown
## Schema 变更流程
1. 提交 PR 修改 org_kg_schema.yaml
2. 数据工程师 Review + 迁移脚本
3. 领域专家签字（重大变更）
4. staging 验证 → prod 发布

## 数据质量 SLA
- 核心 Person/Project 覆盖率 ≥ 95%
- 抽取 Precision ≥ 88%（黄金集）
- 流水线日同步成功率 ≥ 99%

##  incident 响应
- P1：prod 图谱不可用 → 15 min 响应
- P2：质量门禁连续失败 → 1 h 响应
```

---

## 8. 动手练习

1. 实现 `validate_node()` 并对故意错误的 JSON 跑测试
2. 写 2 条 Cypher 质量规则并解释 severity
3. 设计来源优先级表（你的 3 个数据源）
4. 列出 5 条应记入审计日志的操作

---

## 9. 自检清单

- [ ] 理解 L1–L4 质量分层
- [ ] 会写 Schema 校验与 Cypher 完整性规则
- [ ] 知道属性冲突的来源优先级策略
- [ ] 理解置信度阈值与人工复核流程
- [ ] 能设计基本的 RBAC 与审计要求

---

## 下一课

[`08_query_and_api.md`](08_query_and_api.md) — 查询服务与 API 封装
