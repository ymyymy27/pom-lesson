# 第6课：多租户实现：上下文、过滤与防串号

## 1. 一句话解释

多租户实现的关键是"租户上下文贯穿全链路"：HTTP 请求解析出租户，所有数据访问强制带上租户条件，缓存和异步任务也不能丢——任何一步漏掉都可能串租户。

## 2. 类比

酒店房卡：

```
房卡（Token）里写了楼层（tenant_id）
电梯（中间件）只让去自己的楼层
房门（数据访问层）再校验一次
```

## 3. 核心实现

### 3.1 租户从哪里来

| 方式 | 示例 | 适用 |
|------|------|------|
| 域名 | `acme.example.com` | 品牌化 SaaS |
| 路径前缀 | `example.com/acme` | 简单多租户 |
| Header | `X-Tenant-Id` | API / 内部调用 |
| JWT claim | `payload.tenant_id` | 登录后业务请求（推荐） |

### 3.2 中间件链路

```
请求 → 解析租户（域名/Header/JWT）
     → 校验租户状态（启用/过期/配额）
     → 注入上下文（contextvar / ThreadLocal）
     → 控制器 → 服务 → Repository 全程可见
     → 响应前清理上下文（防止线程复用串号）
```

### 3.3 数据访问强制过滤

ORM 层统一处理：

```python
class TenantMixin:
    tenant_id = Column(BigInteger, nullable=False, index=True)

# 所有查询自动追加 tenant_id == current_tenant()
# 所有写入自动填充 tenant_id，禁止信任前端传入
```

数据库 RLS（PostgreSQL）：

```sql
CREATE POLICY tenant_isolation ON tasks
USING (tenant_id = current_setting('app.tenant_id')::bigint);
```

注意：RLS 不等于免检——应用层仍需第一道校验，比如路由到错误的库/表时 RLS 也拦不住（其实是拦得住的，但策略配置错误很难排查，所以双重保险）。

### 3.4 缓存与异步

- Redis key 必须带租户：`tenant:{id}:user:{id}:roles`
- 消息队列任务显式传递 `tenant_id`（contextvar 不跨进程）
- 定时任务逐租户循环执行，禁止"一把梭"跑所有数据

### 3.5 运营能力

- 租户开通/停用/迁移
- 配额：行数、存储、API 调用次数
- 备份策略：共享表全量，独立库/独立 Schema 可按租户
- 灰度开关：新功能按租户放量

## 4. 常见漏洞点

- 注册接口允许自选 `tenant_id`
- 切换租户后没有换 Token，旧租户身份残留
- 聚合统计、导出、报表漏租户条件
- JOIN 关联表时丢失租户过滤
- 线程池复用导致上下文串租户（忘了清理）

## 5. 动手练习

运行 `practice/multitenant_demo.py`：

1. 观察"越权读取其他租户数据"如何被拦截
2. 新增一个 `tenant_report()` 函数，只统计当前租户的数据并跑通

## 6. 自检清单

- [ ] 能说出租户上下文的三种来源及其适用场景
- [ ] 知道为什么缓存 key 必须带租户
- [ ] 能列出至少 4 个容易漏租户过滤的位置
