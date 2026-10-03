# 第2课：Schema 设计与本体建模

> 前置：第 1 课  
> 关联：[`07_quality_and_governance.md`](07_quality_and_governance.md) 治理规范

Schema 是知识图谱的「宪法」。Schema 设计失败，后续抽取、融合、查询全部返工。**本课目标：设计可演进、可治理的 Schema。**

---

## 1. 本体 vs Schema：两层抽象

```
本体层（Ontology）          工程层（Schema）
─────────────────          ─────────────────
Person 是一种 Entity        Label: Person
worksAt 连接 Person→Company  Relation: WORKS_AT
Company 有 name 属性         Property: name (string, required)
```

| 层次 | 关注点 | 产出物 |
|------|--------|--------|
| 本体 | 概念语义、继承、约束 | OWL/RDFS 或设计文档 |
| Schema | 可执行的 Label/Relation/Property | YAML/JSON + Neo4j 约束 |

**工程建议：** 中小项目直接用 **Schema YAML** 作为单一真相源（Single Source of Truth），不必先上完整 OWL 工具链。

---

## 2. Schema 设计五原则

### 2.1 以查询驱动设计（Query-Driven Design）

**错误做法：** 先把所有数据库字段映射成节点属性  
**正确做法：** 列出 Top 10 业务问题 → 反推需要哪些实体和关系

```
业务问题                              需要的 Schema
─────────────────────────────────────────────────────
「某员工参与的所有项目」              Person -WORKS_ON-> Project
「某项目的所有负责人及上级」            Person -REPORTS_TO-> Person
                                      Person -WORKS_ON-> Project
「某部门有哪些在职员工」              Person -MEMBER_OF-> Department
```

### 2.2 实体 vs 属性：何时升格为节点？

| 情况 | 作为属性 | 作为独立节点 |
|------|----------|-------------|
| 值唯一、不需关联查询 | ✅ `Person.city = "杭州"` | |
| 需要反向查询、多对多 | | ✅ `(Person)-[:LIVES_IN]->(City)` |
| 值有自身属性 | | ✅ Company 有 industry、规模 |
| 高频过滤字段 | ✅ 索引属性 | 视查询模式 |

**经验法则：** 若你会问「所有住在杭州的人」或「杭州有哪些公司」，City 应升格为节点。

### 2.3 关系方向与命名

```cypher
// ✅ 统一：动词短语、主动语态、大写蛇形
(Person)-[:WORKS_AT]->(Company)
(Person)-[:REPORTS_TO]->(Person)
(Project)-[:OWNED_BY]->(Person)

// ❌ 避免：方向不一致、语义重复
(Person)-[:EMPLOYED_BY]->(Company)   // 与 WORKS_AT 重复
(Company)-[:HAS_EMPLOYEE]->(Person)  // 与 WORKS_AT 方向冲突
```

**团队规范：** 每个 Relation Type 只保留**一种 canonical 方向**，反向遍历用 Cypher 箭头语法处理。

### 2.4 控制 Schema 复杂度

```
推荐规模（中小项目）：
  Node Labels:   10–30 种
  Relation Types: 15–40 种
  核心属性:      每 Label 5–15 个

超出此规模 → 考虑分层：
  核心层（Core）    — 人员、组织、项目
  扩展层（Extension）— 事件、文档、标签
  临时层（Staging）  — 待审核实体
```

### 2.5 预留治理字段

每个节点建议包含：

```yaml
common_properties:
  id:          string   # 全局唯一 ID（业务主键或 UUID）
  source:      string   # 数据来源：hr_db / doc_extract / manual
  confidence:  float    # 抽取置信度 0–1
  created_at:  datetime
  updated_at:  datetime
  version:     int      # Schema 版本
```

---

## 3. Schema 定义示例（YAML）

`practice/schema/org_kg_schema.yaml`：

```yaml
version: "1.0.0"
domain: org_knowledge_graph

nodes:
  Person:
    description: 公司员工
    properties:
      id:       { type: string, required: true, unique: true }
      name:     { type: string, required: true, indexed: true }
      email:    { type: string, indexed: true }
      title:    { type: string }
      status:   { type: enum, values: [active, inactive] }
    relations_out:
      - WORKS_AT:    { target: Company, properties: [since, role] }
      - MEMBER_OF:   { target: Department }
      - REPORTS_TO:  { target: Person }
      - WORKS_ON:    { target: Project, properties: [role] }

  Company:
    properties:
      id:   { type: string, required: true, unique: true }
      name: { type: string, required: true, indexed: true }

  Department:
    properties:
      id:   { type: string, required: true, unique: true }
      name: { type: string, required: true }
    relations_out:
      - BELONGS_TO: { target: Company }

  Project:
    properties:
      id:     { type: string, required: true, unique: true }
      name:   { type: string, required: true }
      status: { type: enum, values: [planning, active, archived] }
    relations_out:
      - OWNED_BY: { target: Person }
```

---

## 4. Schema 版本管理

```
schema/
├── org_kg_schema.yaml      # 当前版本
├── CHANGELOG.md            # 变更记录
└── migrations/
    ├── v1.0_to_v1.1.md     # 迁移说明
    └── v1.1_to_v1.2.md
```

### 变更类型与策略

| 变更 | 兼容性 | 处理方式 |
|------|--------|----------|
| 新增 Label/Relation | 向后兼容 | 直接发布 |
| 新增可选属性 | 向后兼容 | 默认值 / 回填脚本 |
| 重命名 Relation | 破坏性 | 双写期 + 迁移脚本 |
| 删除 Label | 破坏性 | 先标记 deprecated，下个大版本删除 |
| 拆分节点类型 | 破坏性 | 批量 Cypher 迁移 |

### CHANGELOG 示例

```markdown
## v1.1.0 (2026-03-01)
- Added: Person.status enum
- Added: Project.status enum
- Deprecated: EMPLOYED_BY (use WORKS_AT)

## v1.0.0 (2026-01-15)
- Initial release
```

---

## 5. Neo4j 约束与 Schema 同步

从 YAML 生成约束（第 6 课流水线可自动化）：

```cypher
// 唯一约束
CREATE CONSTRAINT person_id IF NOT EXISTS
FOR (p:Person) REQUIRE p.id IS UNIQUE;

CREATE CONSTRAINT company_id IF NOT EXISTS
FOR (c:Company) REQUIRE c.id IS UNIQUE;

// 查询索引
CREATE INDEX person_name IF NOT EXISTS FOR (p:Person) ON (p.name);
CREATE INDEX person_email IF NOT EXISTS FOR (p:Person) ON (p.email);
```

**注意：** Neo4j 不强制 Relation Type 枚举，需在**应用层 + CI 校验**保证合规。

---

## 6. 反模式清单

| 反模式 | 问题 | 修正 |
|--------|------|------|
| 万能节点 `Thing` | 无法类型化查询 | 明确 Label 分层 |
| 属性存 JSON  blob | 无法索引、难维护 | 拆子节点或固定字段 |
| 关系带 20+ 属性 | 关系变「胖实体」 | 升格中间节点 Event/Role |
| 每数据源一套 Label | 无法融合 | 统一 Canonical Schema + source 属性 |
| 无 id 仅用 name | 同名冲突 | 全局唯一 id + name 作展示 |

---

## 7. 设计工作坊流程（团队落地）

```
Step 1: 领域专家列出 20 个核心概念（30 min）
Step 2: 工程师整理为 Node/Relation 草案（1 h）
Step 3: 写出 10 个 Cypher 查询验证 Schema（1 h）
Step 4: 评审：能否回答所有业务问题？（30 min）
Step 5: 定稿 YAML + 创建 Neo4j 约束（30 min）
```

---

## 8. 动手练习

1. 为你所在领域编写 Schema YAML（至少 4 个 Node、6 种 Relation）
2. 为每个 Node 写 1 条唯一约束 Cypher
3. 设计 1 个「破坏性变更」场景，写 migration 说明
4. 用 [`practice/schema/org_kg_schema.yaml`](practice/schema/org_kg_schema.yaml) 对照检查遗漏字段

---

## 9. 自检清单

- [ ] 能区分本体层与工程 Schema 层
- [ ] 能根据业务问题反推 Schema
- [ ] 知道何时把属性升格为节点
- [ ] 会编写 YAML Schema 并同步 Neo4j 约束
- [ ] 理解 Schema 版本管理与破坏性变更策略

---

## 下一课

[`03_data_acquisition.md`](03_data_acquisition.md) — 多源数据接入策略
