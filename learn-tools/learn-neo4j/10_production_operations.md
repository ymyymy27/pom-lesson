# 第10课：生产运维与故障处理

> 交叉参考：[`learn-redis/10_production_operations.md`](../learn-redis/10_production_operations.md)

---

## 1. 运维职责全景

```
监控告警 → 容量规划 → 备份还原 → 升级迁移 → 故障应急 → 安全审计
```

Neo4j 生产关注：**查询延迟、堆内存/GC、磁盘增长、慢查询、备份成功率**。

---

## 2. 监控指标

| 指标 | 获取方式 | 告警阈值（参考） |
|------|----------|------------------|
| 堆使用 | `CALL dbms.queryJmx('java.lang:type=Memory')` / Prometheus | > 85% 持续 |
| 活跃事务 | `SHOW TRANSACTIONS` | 长时间挂起 |
| 存储大小 | `CALL dbms.queryJmx(...)` / 磁盘 | 磁盘 > 80% |
| 查询延迟 | 应用侧 + `PROFILE` | P99 > SLA |
| 连接数 | Driver metrics / `SHOW CONNECTIONS` | 接近 pool 上限 |

**Neo4j Ops Manager**（Enterprise）或 **Prometheus + neo4j_exporter** 是常见组合。

---

## 3. 慢查询治理

```cypher
// 开启查询日志（neo4j.conf）
// dbms.logs.query.enabled=INFO
// dbms.logs.query.threshold=1s

PROFILE
MATCH (p:Person)-[:REPORTS_TO*1..10]->(x)
RETURN x LIMIT 100;
```

| 步骤 | 动作 |
|------|------|
| 1. 发现 | 日志 / APM / 用户反馈 |
| 2. 分析 | `EXPLAIN` / `PROFILE` |
| 3. 优化 | 加索引、缩深度、改模型 |
| 4. 验证 | 对比 DB Hits 与耗时 |
| 5. 回归 | 纳入 CI 性能测试 |

---

## 4. 备份与还原演练

### 4.1 定期 dump

```bash
# cron 示例：每日 2:00
0 2 * * * docker exec learn-neo4j neo4j-admin database dump neo4j \
  --to-path=/backups --overwrite-destination=false
```

### 4.2 还原（维护窗口）

```bash
neo4j stop
neo4j-admin database load neo4j --from-path=/backups/neo4j.dump --overwrite-destination=true
neo4j start
```

**必须定期做还原演练**——未验证的备份等于没有备份。

---

## 5. 升级策略

| 版本跳跃 | 建议 |
|----------|------|
| 补丁 5.26.x → 5.26.y | 低峰滚动，读 release note |
| 小版本 5.25 → 5.26 | staging 全量验证 + 备份 |
| 大版本 4.x → 5.x | 官方迁移指南，可能需 reindex |

步骤：备份 → staging 升级 → 回归测试 → 生产维护窗口 → 监控 24h。

---

## 6. 常见故障

| 现象 | 可能原因 | 处理 |
|------|----------|------|
| `ServiceUnavailable` | 实例宕机、网络 | 查容器/进程、重启 |
| OOM / GC 停顿 | heap 过大或查询过重 | 调 heap、杀慢查询、优化 Cypher |
| 磁盘满 | 日志/事务日志膨胀 | 清日志、扩容、compact |
| 约束冲突激增 | 上游重复 id | 修复 ETL，MERGE 幂等 |
| 锁等待 | 长写事务 | `SHOW TRANSACTIONS` / `TERMINATE` |
| 导入极慢 | 缺索引、单大批次 | 先索引、分批 UNWIND |

```cypher
// 查看并终止长事务（谨慎）
SHOW TRANSACTIONS;
TERMINATE TRANSACTION 'transaction-id';
```

---

## 7. 高可用（Enterprise 概要）

Community 为**单实例**；生产 HA 选项：

- **Neo4j Causal Cluster**：1 Leader + N Follower，自动 failover
- **Aura Professional**：托管 HA
- **应用层读写分离**：Follower 只读（驱动 routing）

```
         ┌─────────┐
  App ──→│ Routing │──→ Leader（写）
         │ Driver  │──→ Follower（读）
         └─────────┘
```

---

## 8. 团队协作清单

| 角色 | 职责 |
|------|------|
| 开发 | Cypher 评审、索引变更 PR、禁止生产 Browser 裸删 |
| DBA/SRE | 备份、监控、升级、容量 |
| 数据 | Schema 版本、迁移脚本、质量指标 |

**变更窗口：** Schema（约束/索引）变更需先在 staging `PROFILE` 验证锁表时间。

---

## 9. 生产就绪检查表

- [ ] UNIQUE 约束覆盖所有业务主键
- [ ] 热路径查询有 PROFILE 记录
- [ ] 备份 cron + 季度还原演练
- [ ] 密码/URI 走密钥管理
- [ ] Bolt  TLS 或内网隔离
- [ ] 慢查询日志 threshold 已开
- [ ] 环境分实例/分库，无 prod 数据在 dev
- [ ] 事故 runbook（宕机、还原、回滚）

---

## 10. 继续学习

| 方向 | 资源 |
|------|------|
| 知识图谱工程 | [`learn-knowledge-graph`](../../learn-ai/learn-knowledge-graph/) |
| Graph RAG | stage-08 Graph RAG |
| 图算法 | Neo4j GDS 官方文档 |
| 系统设计案例 | `learn-se` |

---

## 课程总结

完成本教程后，你应能：

1. 用 Cypher 建模、查询、优化 Neo4j
2. 用 Python 驱动集成到 FastAPI
3. 规划多环境隔离与 Docker/Aura 部署
4. 执行备份、监控与常见故障处理

**建议路径：** `learn-neo4j` → `learn-knowledge-graph` 第 4–10 课 → Graph RAG 消费侧。
