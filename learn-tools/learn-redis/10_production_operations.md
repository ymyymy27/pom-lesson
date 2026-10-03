# 第10课：生产运维、高可用与故障处理

> 前置：第 7–9 课 · 第 4 课（雪崩对策）  
> 关联：[`learn-se/learn-system-design`](../../learn-se/learn-system-design/) 架构案例

本课面向「Redis 已上线、要对 SLA 负责」的场景：内存与淘汰、持久化与恢复、主从与 Sentinel、Cluster 选型、监控告警、典型故障处理。

---

## 1. 生产 Redis 在架构中的位置

```
                    ┌─────────────┐
  用户请求 ────────→│  Web / API  │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │PostgreSQL│ │  Redis   │ │  其他    │
        │ 权威数据  │ │ 缓存/会话 │ │  MQ...   │
        └──────────┘ └────┬─────┘ └──────────┘
                          │
              Redis 挂了会怎样？
              ├── 缓存：穿透到 DB，变慢但可能可用（降级）
              ├── Session：全员登出（若没 sticky + 多副本）
              ├── 限流：可能失效（安全风险）
              ├── Celery：任务堆积/失败
              └── 分布式锁：可能双写（严重）
```

**设计原则：** Redis 是**性能与状态加速层**， rarely 是唯一数据源（Session、队列除外需额外保障）。

---

## 2. 内存管理与淘汰策略

### 2.1 为什么必须设 maxmemory

Redis 是**内存数据库**。不设上限时，内存写满会导致：

- OOM Killer 杀进程（Linux）
- 系统整体不稳定

```conf
maxmemory 2gb
maxmemory-policy allkeys-lru
```

### 2.2 淘汰策略对照

| 策略 | 行为 | 适用 |
|------|------|------|
| `noeviction` | 写满返回 OOM 错误 | 队列、不可丢数据 |
| `allkeys-lru` | 所有 key 中 LRU 淘汰 | **通用缓存**（最常见） |
| `volatile-lru` | 仅淘汰设了 TTL 的 key | 混合永久+临时 key |
| `allkeys-lfu` | 访问频率低优先淘汰 | 热点明确 |
| `volatile-ttl` | 优先淘汰 TTL 短的 | 临时数据为主 |

```bash
CONFIG GET maxmemory
CONFIG GET maxmemory-policy
INFO memory
```

### 2.3 内存排查

```bash
INFO memory
# used_memory_human — 当前使用
# used_memory_peak_human — 历史峰值
# mem_fragmentation_ratio — >1.5 可能碎片严重

MEMORY USAGE myapp:cache:article:42    # 单 key 占用（Redis 4.0+）
```

**大 key 危害：** 单 key 几 MB → 删除/序列化阻塞单线程 → 延迟尖刺。

```bash
# 开发环境找大 key（生产慎用）
redis-cli --bigkeys
```

**对策：** 拆 key、压缩、Hash 分桶、只存 ID 列表。

---

## 3. 持久化与备份恢复

### 3.1 RDB 快照

```conf
save 900 1      # 900 秒内 ≥1 次写入则快照
save 300 10
save 60 10000
dbfilename dump.rdb
dir /data
```

```bash
BGSAVE              # 后台快照
LASTSAVE            # 上次成功时间
```

**特点：** 恢复快；两次快照间可能丢数据。

### 3.2 AOF 日志

```conf
appendonly yes
appendfsync everysec    # 每秒 fsync，最多丢 1 秒
# appendfsync always    # 最安全，最慢
# appendfsync no        # 快，可能丢较多
```

```bash
BGREWRITEAOF        # 重写 AOF，压缩体积
INFO persistence
```

### 3.3 生产推荐

| 场景 | 建议 |
|------|------|
| 纯缓存（可重建） | 可不开持久化，或仅 RDB |
| Session / 队列 | AOF everysec + 备份 |
| 金融级 | 主从 + AOF always 或托管服务 |

### 3.4 备份流程

```bash
# 1. 触发后台保存
redis-cli BGSAVE

# 2. 复制 RDB（容器示例）
docker cp learn-redis:/data/dump.rdb ./backup/

# 3. 云托管：使用厂商自动备份 + PITR
```

### 3.5 恢复

```bash
# 停止 Redis → 替换 dump.rdb / appendonly.aof → 启动
# 注意：恢复会覆盖当前数据，先在 staging 验证
```

---

## 4. 高可用：主从、Sentinel、Cluster

### 4.1 单机的问题

- 进程挂 → 全不可用
- 机器挂 → 数据可能丢（取决于持久化）
- 内存单点上限

### 4.2 主从复制（Replication）

```
        ┌─────────┐
        │ Master  │ ← 写 + 读（可选）
        └────┬────┘
             │ 异步复制
     ┌───────┴───────┐
     ▼               ▼
┌─────────┐    ┌─────────┐
│ Replica │    │ Replica │ ← 读扩展、故障备份
└─────────┘    └─────────┘
```

```conf
# replica 节点
replicaof master_host 6379
replica-read-only yes
```

**注意：** 主从异步复制有**短暂不一致**；master 宕机未同步的数据可能丢。

### 4.3 Sentinel（自动故障转移）

```
┌──────────┐  ┌──────────┐  ┌──────────┐
│Sentinel 1│  │Sentinel 2│  │Sentinel 3│  监控 + 投票
└────┬─────┘  └────┬─────┘  └────┬─────┘
     └─────────────┼─────────────┘
                   ▼
              Master / Replica
```

- 至少 **3 个 Sentinel**（奇数，防脑裂）
- Master 宕机 → Sentinel 提升 Replica 为新 Master
- 客户端连接 Sentinel 获取当前 Master 地址（redis-py `Sentinel` 类）

**适用：** 数据量可单机容纳、需要 HA、读写分离。

### 4.4 Cluster（分片）

```
┌─────────┐  ┌─────────┐  ┌─────────┐
│ Node 1  │  │ Node 2  │  │ Node 3  │  16384 slots 分片
│ slot    │  │ slot    │  │ slot    │
│ 0-5460  │  │5461-10922│ │10923-.. │
└─────────┘  └─────────┘  └─────────┘
```

- **数据分片**到多节点，突破单机内存
- **只支持 db0**（见第 7 课）
- 客户端需 Cluster 感知（`RedisCluster`）
- 运维复杂度高

**选型建议：**

| 需求 | 方案 |
|------|------|
| 学习 / 小项目 | 单机 |
| 生产 HA，数据 < 单机内存 | 主从 + Sentinel |
| 数据量超大 / 写 QPS 极高 | Cluster |
| 不想自运维 | 云 Redis（AWS ElastiCache、阿里云 Redis 等） |

### 4.5 与缓存雪崩的关系（第 4 课回顾）

Redis 整体不可用 → 全部打到 DB → **缓存雪崩**。

对策：

- Sentinel / Cluster 提高可用性
- 限流 + 降级（Redis 不可用时只读静态页 / 返回 503）
- TTL 加 jitter，避免同时过期

---

## 5. 监控与告警

### 5.1 必监控指标

| 指标 | 命令 / 来源 | 告警阈值（示例） |
|------|-------------|------------------|
| 存活 | `PING` | 失败即 P0 |
| 内存使用率 | `INFO memory` | > 80% 警告，> 90% 严重 |
| 连接数 | `INFO clients` | 接近 maxclients |
| 命中率 | keyspace hits/misses | 骤降 |
| 延迟 | `LATENCY DOCTOR` | p99 > 10ms |
| 复制 lag | `INFO replication` | offset 差持续增大 |
| 拒绝连接 / OOM | `INFO stats` | rejected_connections > 0 |
| 慢查询 | `SLOWLOG GET` | 频繁 > 10ms 命令 |

### 5.2 常用命令

```bash
INFO stats
INFO replication
INFO commandstats
SLOWLOG GET 10
CLIENT LIST
LATENCY DOCTOR
```

### 5.3 应用层指标

- 缓存命中率 = hits / (hits + misses)
- Redis 操作耗时（OpenTelemetry / Prometheus histogram）
- `/health` 中 redis 状态

### 5.4 日志与审计

- 慢查询日志持久化分析
- ACL 日志（Redis 6+）
- 变更操作（CONFIG SET、FLUSH）审计

---

## 6. 性能与稳定性

### 6.1 单线程模型

Redis 命令**原子串行**执行。一个慢命令阻塞全体：

| 危险命令 | 原因 |
|----------|------|
| `KEYS *` | O(N) 遍历 |
| `FLUSHALL` | 清空 |
| 大 key `DEL` | 释放大块内存 |
| `SUNION` 超大 set | 计算量大 |

**替代：** `SCAN`、`UNLINK`（异步删，4.0+）、分批处理。

### 6.2 Pipeline 与连接数

```python
pipe = r.pipeline()
for i in range(1000):
    pipe.set(f"k:{i}", i)
pipe.execute()
```

- Pipeline 减少 RTT，**不保证原子**（与 MULTI/EXEC 不同）
- 连接池 `max_connections` 按 QPS 与慢查询调优

### 6.3 热 key 问题

某 key QPS 极高 → 单线程瓶颈 / Cluster 单 slot 热点。

对策：

- 本地缓存（L1）挡一层
- 热 key 拆分为 `key:0` `key:1` ... 随机读
- Read replica 读扩展

---

## 7. 典型故障 playbook

### 7.1 Redis 完全不可用

**现象：** `/health` degraded，应用报 `ConnectionError`。

**排查：**

```bash
docker ps -a | findstr redis
redis-cli PING
INFO server
```

**处理：**

1. 重启 / 故障转移（Sentinel）
2. 应用降级：跳过缓存直读 DB（限流保护 DB）
3. 恢复后观察 DB 负载

### 7.2 内存满 / OOM

**现象：** `OOM command not allowed` 或进程被 kill。

**处理：**

1. `INFO memory` 确认 used / maxmemory
2. `--bigkeys` 找大 key
3. 调整 `maxmemory-policy` 或扩容
4. 紧急：`SCAN` + `UNLINK` 非核心 prefix（勿 FLUSHALL）

### 7.3 缓存命中率骤降

**可能原因：**

- 大量 key 同时过期（雪崩）
- 部署后 prefix 变更
- 连接到了错误实例 / db
- 缓存被 FLUSH

**排查：** 对比 `INFO stats` keyspace_hits/misses；查部署变更；查 MONITOR（dev）。

### 7.4 主从不一致 / 复制中断

```bash
INFO replication
# master_link_status:down → 检查网络、密码、磁盘
```

**处理：** 修复网络；`PSYNC` 重同步；必要时 rebuild replica。

### 7.5 Session 全员失效

**原因：** Redis 重启无持久化、FLUSH、切换实例、TTL 统一过短。

**预防：** AOF、Session 持久化或 JWT+短黑名单、滚动重启。

---

## 8. 安全运维清单

### 8.1 上线前

- [ ] 密码 / ACL
- [ ] maxmemory + eviction policy
- [ ] 持久化策略与备份
- [ ] 不暴露公网 6379
- [ ] 禁用危险命令（rename-command FLUSHALL ""）
- [ ] 监控告警接入
- [ ] 故障降级方案已测试

### 8.2 变更时

- [ ] staging 先验证
- [ ] 大版本升级看 release note
- [ ] 备份后再 `CONFIG SET`
- [ ] 低峰期执行 BGREWRITEAOF / 重启

### 8.3 定期

- [ ] 备份恢复演练（季度）
- [ ] 慢查询 review
- [ ] 内存与 bigkey 巡检
- [ ] Key 注册表与代码一致

---

## 9. 托管 Redis vs 自建

| 维度 | 自建（Docker/VM） | 云托管 |
|------|-------------------|--------|
| 运维成本 | 团队负责 | 厂商负责 HA、备份 |
| 灵活性 | 完全控制 | 受限于产品功能 |
| 学习价值 | 高 | 中 |
| 生产推荐 | 小团队慎用单机 | **多数团队首选** |

学习阶段用 Docker；生产优先评估托管，除非有专职 DBA/SRE。

---

## 10. 练习

1. 对本地 `learn-redis` 执行 `INFO memory`、`INFO stats`、`INFO persistence`，记录三项关键字段含义
2. 设置 `maxmemory 50mb` + `allkeys-lru`，写入大量 key 观察淘汰行为（**仅本地**）
3. 用 `SLOWLOG` 模拟一条慢查询（如 debug 下 `KEYS *`），理解为何生产禁用
4. 写一份「Redis 宕机 5 分钟」的降级方案：Session、缓存、Celery 分别怎么处理
5. 对比：你的项目适合单机 / Sentinel / Cluster / 托管？写 200 字理由

---

## 11. 本课 Checklist

- [ ] 理解 maxmemory 与淘汰策略
- [ ] 能解释 RDB vs AOF 取舍
- [ ] 知道 Sentinel 与 Cluster 的适用场景
- [ ] 能列出 5 个必监控指标
- [ ] 知道 KEYS *、大 key、FLUSHALL 的风险
- [ ] 有基本故障排查命令清单

---

## 课程总结（learn-redis 全 10 课）

| 阶段 | 课程 | 能力 |
|------|------|------|
| 基础 | 00–02 | 命令、数据结构 |
| 开发 | 03–06 | Python、缓存模式、实战 |
| **工程** | **07–10** | **逻辑库、部署、协作、运维** |

**速查：** [`00_redis_syntax.md`](00_redis_syntax.md)

**继续深入：**

| 方向 | 资源 |
|------|------|
| 容器部署 | `learn-docker/05_practical_deploy.md` |
| Django + Celery | `learn-fullstack/stage-06-celery-cache` |
| 系统设计 | `learn-se/learn-system-design` |
