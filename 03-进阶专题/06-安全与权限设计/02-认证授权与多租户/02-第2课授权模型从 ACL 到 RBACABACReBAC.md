> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第2课：授权模型：从 ACL 到 RBAC、ABAC、ReBAC

## 1. 一句话解释

授权模型回答"谁能对什么资源做什么操作"，RBAC 用"角色"做中间层，是大多数业务系统的最佳起点；ABAC 和 ReBAC 是在复杂规则或关系链场景下的进阶选择。

## 2. 类比

图书馆借阅：

```
ACL  = 每本书登记"谁能借"，人一多就爆炸
RBAC = 发"教师卡/学生卡"，卡片决定能进哪些书架
ABAC = "晚上 9 点后学生不能进阅览室"这类动态规则
ReBAC = "能借你导师借过的书"这类关系链规则
```

## 3. 核心知识

### 3.1 ACL（访问控制列表）

用户直接绑定权限：`user → permission`。

优点：简单、直观。缺点：用户一多管理失控，几乎不做唯一方案。

### 3.2 RBAC（基于角色的访问控制）

核心链路：

```
User → Role → Permission → Resource
```

标准模型 RBAC0-3：

| 模型 | 能力 |
|------|------|
| RBAC0 | 用户-角色-权限基础模型 |
| RBAC1 | 角色继承（管理员继承普通角色权限） |
| RBAC2 | 职责分离（不能同时是出纳和会计） |
| RBAC3 | RBAC1 + RBAC2 |

最小表结构：

```sql
CREATE TABLE users (id BIGSERIAL PRIMARY KEY, email TEXT UNIQUE);
CREATE TABLE roles (id BIGSERIAL PRIMARY KEY, code TEXT, name TEXT);
CREATE TABLE permissions (id BIGSERIAL PRIMARY KEY, code TEXT);
CREATE TABLE user_roles (user_id BIGINT, role_id BIGINT, PRIMARY KEY(user_id, role_id));
CREATE TABLE role_permissions (role_id BIGINT, permission_id BIGINT, PRIMARY KEY(role_id, permission_id));
```

### 3.3 权限点命名规范

统一为 `资源:动作`：

```
project:create / project:read / project:update / project:delete
task:create / task:read / task:update / task:delete / task:assign
member:invite / member:remove / role:manage
```

规则：

- 支持通配符（`project:*`），但尽量显式列出
- 权限点里不要带数字 ID（`project:42:delete` 是反模式）
- 所有权限点注册在权限中心，业务代码只引用 code

### 3.4 ABAC（基于属性的访问控制）

基于用户属性、资源属性、环境条件动态决策：

```json
{
  "effect": "allow",
  "action": "approve_expense",
  "conditions": {
    "subject.department": ["==", "resource.department"],
    "subject.role": ["in", ["manager", "finance"]],
    "environment.time": ["between", ["09:00", "18:00"]]
  }
}
```

优点：灵活、表达力强。缺点：规则难调试、性能开销大、权限"不可预测"。

### 3.5 ReBAC（基于关系的访问控制）

Google Zanzibar 风格：把"谁能访问什么"建模为图中的可达性问题。适合社交、文档协作、项目关系链等场景（"能访问你下属创建的项目"）。

## 4. 选型矩阵

| 场景 | 推荐 |
|------|------|
| 小型后台、管理端 | RBAC |
| 多组织 + 细粒度数据 | RBAC + 数据权限（第4课） |
| 合规复杂、规则频繁变化 | ABAC |
| 协作/文档/社交关系链 | ReBAC |

大多数 SaaS 的合理起点：**RBAC + 数据权限**，先跑通，再按需引入 ABAC 规则引擎。

## 5. 动手练习

为 TaskFlow 设计权限点与角色矩阵：

1. 列出至少 12 个权限点（覆盖 project、task、comment、member）
2. 设计 3 个内置角色（Owner / Admin / Member）的权限矩阵
3. 画 ER 图：users、roles、permissions、user_roles、role_permissions

思考：Owner 和 Admin 的差别应该体现在哪里？（通常：Owner 能管理租户、转让、删除，Admin 只管业务配置）

## 6. 自检清单

- [ ] 能画出 RBAC 的 ER 图并解释 RBAC0/1/2 的区别
- [ ] 能说出 ABAC 与 RBAC 各自的优缺点和适用场景
- [ ] 知道权限点为什么不能包含业务 ID
