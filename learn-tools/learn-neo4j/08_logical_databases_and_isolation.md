# 第8课：逻辑数据库与环境隔离

> 交叉参考：[`learn-redis/07_logical_databases_and_isolation.md`](../learn-redis/07_logical_databases_and_isolation.md)

Neo4j 4.0+ 支持**单实例多 database**，类似 Redis 的 db0–db15，但语义更接近「独立图空间」。

---

## 1. 多 Database 模型

```
Neo4j 实例
├── system      — 系统库（管理用，勿写业务数据）
├── neo4j       — 默认库
├── org_dev     — 开发环境组织图谱
├── org_staging — 预发
└── org_prod    — 生产（或独立实例）
```

| 特性 | Neo4j Database | Redis 逻辑库 |
|------|----------------|--------------|
| 数据隔离 | 完全隔离节点/关系 | 完全隔离 Key |
| 跨库查询 | ❌ 不支持 JOIN | ❌ 不支持 |
| 备份粒度 | 可按库 | 按实例 |
| 切换方式 | `session(database=...)` | `SELECT n` |

---

## 2. 创建与管理

```cypher
// system 库或管理权限下
CREATE DATABASE org_dev IF NOT EXISTS;
CREATE DATABASE org_staging IF NOT EXISTS;
SHOW DATABASES;
```

Browser：`:use org_dev`

Python：

```python
with driver.session(database="org_dev") as session:
    session.run("MATCH (n) RETURN count(n) AS c")
```

---

## 3. 环境隔离策略

| 策略 | 适用 | 说明 |
|------|------|------|
| **分实例** | 生产 | 最强隔离，独立资源与备份 |
| **分 database** | dev/staging 共用一台 | 成本低，Community 可用 |
| **Label 前缀** | 仅临时/demo | `Dev_Person` — 易出错，不推荐生产 |
| **Aura 多实例** | 云托管 | 按环境各建 Aura 实例 |

**推荐：**

```
开发/测试  → 单实例多库（org_dev, org_test）
预发       → 独立实例或独立 Aura
生产       → 独立实例 + 只读副本（Enterprise）
```

---

## 4. 配置约定

### 4.1 环境变量

```bash
# .env
NEO4J_URI=bolt://localhost:7687
NEO4J_DATABASE=org_dev
NEO4J_USER=neo4j
NEO4J_PASSWORD=changeme
```

### 4.2 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| Database 名 | 小写+下划线 | `kg_dev`, `org_prod` |
| Label | PascalCase 单数 | `Person`, `Project` |
| 关系类型 | UPPER_SNAKE | `WORKS_ON`, `MEMBER_OF` |
| 业务 id | 前缀+序号 | `person_001`, `proj_order` |

**勿**用环境名做 Label（`Dev_Person`），否则查询与迁移痛苦。

---

## 5. 迁移与种子数据

```bash
# 开发库灌数
NEO4J_DATABASE=org_dev python seed_demo_graph.py

# 切库验证
docker exec learn-neo4j cypher-shell -u neo4j -p changeme \
  -d org_dev "MATCH (n) RETURN count(n)"
```

跨环境迁移：备份还原（第 9 课）或 `neo4j-admin dump/load`，而非混在一个库里用 Label 区分。

---

## 6. 团队协作

| 场景 | 做法 |
|------|------|
| 本地开发 | 每人 `org_dev` 或 docker 独立 volume |
| CI 测试 |  ephemeral 容器 + 临时库，测完销毁 |
| 共享 staging | 固定 `org_staging`，禁止 `DETACH DELETE` 无 WHERE |
| Schema 变更 | Git 管理 Cypher 迁移脚本，顺序执行 |

迁移脚本示例 `migrations/001_add_person_email_index.cypher`：

```cypher
CREATE INDEX person_email IF NOT EXISTS FOR (p:Person) ON (p.email);
```

---

## 7. 动手练习

1. 创建 `org_test` database（若 Community 支持；否则用默认库模拟命名约定）
2. 配置 `.env` 的 `NEO4J_DATABASE`，seed 后验证数据隔离
3. 列出团队应遵守的 Label / 关系命名规范（3 条即可）

---

## 8. 自检清单

- [ ] 理解 database 与 Redis db 的异同
- [ ] 环境优先分实例/分库，而非 Label 前缀
- [ ] 应用通过环境变量切换 database
- [ ] 有 Schema 迁移脚本的意识

---

## 下一课

[`09_deployment_and_environments.md`](09_deployment_and_environments.md) — 部署与环境配置
