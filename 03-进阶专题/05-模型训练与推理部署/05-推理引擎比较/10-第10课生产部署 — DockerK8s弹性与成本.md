> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第10课：生产部署 — Docker、K8s、弹性与成本

> 上一课：[`09-第9课思考型模型（Reasoning Models）的推理服务.md`](<09-第9课思考型模型（Reasoning Models）的推理服务.md>)

---

## 1. 生产部署清单

上线前逐项确认：

- [ ] 鉴权与网络隔离（API Key、VPC、白名单）
- [ ] 资源限制（显存、max-num-seqs、超时）
- [ ] 健康检查与就绪探针
- [ ] 监控告警（TTFT/TPOT/排队/显存）
- [ ] 日志与 Trace（请求 ID 贯穿）
- [ ] 模型文件版本与回滚方案
- [ ] 压测基线文档

---

## 2. Docker 部署

```yaml
# docker-compose.yml（示例，NVIDIA GPU）
services:
  vllm:
    image: vllm/vllm-openai:latest
    ports:
      - "8000:8000"
    environment:
      - HF_HOME=/root/.cache/huggingface
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    command: >
      --model Qwen/Qwen2.5-7B-Instruct
      --max-model-len 8192
      --gpu-memory-utilization 0.9
      --api-key ${VLLM_API_KEY}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 120s
```

完整可运行版本见 `practice/docker-compose.yml`。

---

## 3. Kubernetes 部署要点

### GPU 调度

```yaml
resources:
  limits:
    nvidia.com/gpu: 1
```

配合 device plugin（NVIDIA GPU Operator）实现 GPU 分配。

### 弹性扩缩容

| 触发器 | 说明 |
|--------|------|
| 自定义指标 | 排队请求数、GPU 利用率 |
| 时间窗口 | 业务高峰/低谷 |
| 请求量 | QPS（注意与并发区分） |

> 注意：推理服务加载模型慢（分钟级），扩缩容要预热；可用「常驻基数 + 突发池」策略。

### 版本与回滚

模型即版本：镜像 tag / 模型路径 / engine 版本三者绑定，灰度验证后再全量。

---

## 4. 多卡与多副本

```
单副本大模型（TP=4）     多副本小模型
─────────────────      ─────────────────
4×GPU 服务一个 70B       每个副本 1×GPU 服务 7B
吞吐高，弹性粒度大        按副本弹性，故障域小
```

选型逻辑：

- 模型单卡放不下 → TP/PP/EP
- 模型单卡能放下、并发是瓶颈 → 多副本 + 负载均衡

---

## 5. 成本优化

### 算力成本

| 手段 | 收益 |
|------|------|
| 量化（FP8/INT4） | 省显存、可提升密度 |
| 前缀缓存 | 省 prefill 算力 |
| PD 分离 | prefill/decode 独立伸缩 |
| 模型分级路由 | 简单请求走小模型 |
| 空闲缩容 | 低峰期停副本 |
| 批量任务离线 | 不占在线资源 |

### 单位成本指标

用**每百万 token 成本**而不是 GPU 数量做决策：

```
成本效率 = 总成本 / 服务 token 总量
```

---

## 6. 安全与治理

- 模型文件校验（hash、来源可信）
- API 限流与配额（按租户/应用）
- Prompt 注入与敏感信息过滤（见 [`03-进阶专题/06-安全与权限设计/01-安全基础/04-第4课LLM 与 Agentic AI 安全.md`](<../../06-安全与权限设计/01-安全基础/04-第4课LLM 与 Agentic AI 安全.md>)）
- 日志脱敏（思考链可能包含业务敏感信息）
- 审计：谁在什么时间调用了什么模型、花了多少 token

---

## 7. 事故复盘模板

```
现象：___ 开始，___ 恢复
指标：TTFT P99 从 ___ 到 ___
根因：___
缓解：___
预防：___
```

常见根因：GPU 显存碎片、并发超过甜点、模型热加载、缓存失效、上游网络。

---

## 8. 动手练习

1. 在 `practice/` 下用 docker compose 启动 vLLM（需 GPU），验证健康检查
2. 设计一份「30 天推理服务容量规划」：预估 QPS、平均输入/输出 token，反推 GPU 数量
3. 给团队写一页部署检查单（基于第 1 节清单）

---

## 9. 自检清单

- [ ] 能给出推理服务的生产部署清单
- [ ] 能配置 Docker GPU 资源与健康检查
- [ ] 知道 K8s GPU 调度与弹性扩缩容要点
- [ ] 能区分「单副本大模型」与「多副本小模型」的取舍
- [ ] 能用单位 token 成本评估部署方案
- [ ] 能识别推理服务的安全与审计要求

---

## 课程完结

回到 [`课程说明.md`](课程说明.md) 复习课程地图；有 GPU 时把第 3、4、8 课的练习完整跑一遍，你就具备了独立交付推理服务的能力。
