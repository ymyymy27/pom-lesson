> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第2课：DevOps 与 CI/CD

## 1. DevOps 是什么？

### 一句话解释
**DevOps 是开发（Dev）和运维（Ops）之间的文化、实践和工具链** —— 让软件从代码到上线更快、更可靠。

### 传统问题

```
开发：「代码写完了，部署吧！」
运维：「你的代码把生产搞崩了！」
开发：「在我电脑上能跑啊...」
      ↓
   互相甩锅、发布慢、质量差
```

### DevOps 目标

```
         开发                运维
          │                  │
          └──── DevOps ──────┘
                    │
          快速交付 + 稳定运行
```

**CALMS 模型：**

| 字母 | 含义 |
|------|------|
| C | Culture（文化）— 协作、共担责任 |
| A | Automation（自动化）— 减少手工操作 |
| L | Lean（精益）— 消除浪费 |
| M | Measurement（度量）— 数据驱动 |
| S | Sharing（共享）— 知识、工具共享 |

---

## 2. CI/CD 流水线

### 概念

```
CI (Continuous Integration)     — 持续集成
  开发者频繁合并代码 → 自动构建 + 自动测试

CD (Continuous Delivery)        — 持续交付
  代码随时可部署到生产（手动触发）

CD (Continuous Deployment)      — 持续部署
  代码自动部署到生产（全自动）
```

### 完整流水线

```
Code Push / PR
      │
      ▼
┌─────────────┐
│   Lint      │  代码风格检查
├─────────────┤
│   Build     │  编译/打包
├─────────────┤
│   Unit Test │  单元测试
├─────────────┤
│   Integration│ 集成测试
├─────────────┤
│   Security  │  安全扫描（SAST/依赖检查）
├─────────────┤
│   Build     │  构建 Docker 镜像
│   Image     │
├─────────────┤
│   Deploy    │  部署到 Staging
│   Staging   │
├─────────────┤
│   E2E Test  │  端到端测试
├─────────────┤
│   Deploy    │  部署到 Production
│   Production│
└─────────────┘
```

### GitHub Actions 示例

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -r requirements.txt -r requirements-dev.txt

      - name: Lint
        run: ruff check .

      - name: Type check
        run: mypy src/

      - name: Test
        run: pytest --cov=src --cov-fail-under=80

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build and push Docker image
        run: |
          docker build -t myapp:${{ github.sha }} .
          docker push myapp:${{ github.sha }}

      - name: Deploy to production
        run: echo "Deploy myapp:${{ github.sha }}"
```

---

## 3. 部署策略

### 3.1 滚动部署（Rolling Update）

```
v1 v1 v1 v1  →  v2 v1 v1 v1  →  v2 v2 v1 v1  →  v2 v2 v2 v2
逐个替换实例，始终有服务可用
```

**优点：** 简单、无额外资源  
**缺点：** 版本共存期间可能不一致

### 3.2 蓝绿部署（Blue-Green）

```
Load Balancer
      │
  ┌───┴───┐
  ▼       ▼
Blue(v1) Green(v2)    ← 同时运行两套
  ↑ 活跃
         切换 → Green 活跃，Blue 待命回滚
```

**优点：** 瞬间切换、快速回滚  
**缺点：** 双倍资源

### 3.3 金丝雀部署（Canary）

```
95% 流量 → v1（稳定版）
 5% 流量 → v2（新版）

监控 v2 无异常 → 逐步增加到 100%
```

**优点：** 风险最小、渐进验证  
**缺点：** 需要流量控制和监控

### 3.4 功能开关（Feature Flag）

```python
if feature_flags.is_enabled("new_checkout", user_id):
    return new_checkout_flow()
else:
    return old_checkout_flow()
```

**优点：** 代码已部署但功能未开放，随时开关  
**工具：** LaunchDarkly, Unleash, 自建

### 策略选型

```
风险低、资源有限？     → 滚动部署
需要快速回滚？         → 蓝绿
高风险大变更？         → 金丝雀 + Feature Flag
```

---

## 4. 基础设施即代码（IaC）

### 定义
用代码定义和管理基础设施，而非手动操作。

```yaml
# docker-compose.yml — 最简单的 IaC
services:
  app:
    image: myapp:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgres://db:5432/myapp
    depends_on:
      - db

  db:
    image: postgres:15
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

**工具链：**

| 工具 | 用途 |
|------|------|
| Docker Compose | 本地/小型部署 |
| Terraform | 云资源（AWS/GCP/Azure） |
| Ansible | 配置管理 |
| Kubernetes + Helm | 容器编排 |
| Pulumi | 用编程语言写 IaC |

---

## 5. 监控与告警

### 三个黄金信号（Google SRE）

| 信号 | 含义 | 示例指标 |
|------|------|---------|
| Latency | 请求延迟 | P99 响应时间 |
| Traffic | 流量 | QPS、并发连接 |
| Errors | 错误率 | 5xx 比例 |

加上：**Saturation**（饱和度）— CPU/内存/磁盘使用率

### 告警原则

```
好的告警：需要人立即行动
坏的告警：「CPU > 50%」每天响 100 次 → 告警疲劳 → 真问题被忽略
```

**On-Call 最佳实践：**
- 告警分级（P0 立即 / P1 工作时间内 / P2 下个 Sprint）
- Runbook：每个告警怎么处理
- 事后复盘（Blameless Postmortem）

---

## 6. DevOps 成熟度

```
Level 0: 手工部署，无自动化测试
Level 1: 有 CI（自动构建+测试）
Level 2: 有 CD（自动部署到 Staging）
Level 3: 持续部署到生产 + 监控
Level 4: 全面自动化 + 自愈 + 混沌工程
```

**建议路径：** 先 CI → 再 CD 到 Staging → 再加生产部署 → 最后加监控和高级策略。

---

## 7. 动手练习

### 练习 1：设计 CI 流水线

为一个 Python FastAPI 项目设计 CI 步骤，列出每个步骤的检查内容和失败时的处理。

### 练习 2：部署策略选择

以下场景选什么部署策略？

1. 修改 CSS 样式
2. 重构支付核心逻辑
3. 数据库 Schema 大变更

<details>
<summary>参考答案</summary>

1. **滚动部署** — 低风险，直接滚
2. **金丝雀 + Feature Flag** — 高风险，渐进验证
3. **蓝绿 + 数据迁移脚本** — 需要可回滚，Schema 变更需兼容

</details>

---

## 8. 自检清单

- [ ] 能解释 CI、CD（Delivery）、CD（Deployment）的区别
- [ ] 能描述一个完整的 CI/CD 流水线
- [ ] 知道四种部署策略及其适用场景
- [ ] 理解 IaC 的概念和常用工具
- [ ] 知道 Google SRE 三个黄金信号

---

## 9. 延伸阅读

- 《The DevOps Handbook》— Kim, Humble, Debois, Willis
- 《Site Reliability Engineering》— Google SRE Book（免费在线）
- 关联：`03-进阶专题/02-部署与工程运维/Docker/` — 容器化
- 关联：`05-公共资源/命令速查/Git/` — 版本控制
- 下一课：`03-第3课协作工作流.md`
