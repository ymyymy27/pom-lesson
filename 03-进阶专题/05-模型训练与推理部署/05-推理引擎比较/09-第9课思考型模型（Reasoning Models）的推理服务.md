> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第9课：思考型模型（Reasoning Models）的推理服务

> 上一课：[`08-第8课压测指标与参数调优.md`](08-第8课压测指标与参数调优.md) · 下一课：[`10-第10课生产部署 — DockerK8s弹性与成本.md`](<10-第10课生产部署 — DockerK8s弹性与成本.md>)

---

## 1. 什么是思考型模型

以 OpenAI o 系列、DeepSeek-R1、Qwen3（Thinking 模式）为代表的模型，会在正式回答前生成一段**思考链（CoT）**：

```
用户提问
  │
  ▼
[思考 tokens：内部推理过程]（可能数千 token）
  │
  ▼
[正式回答]
```

服务侧的新挑战：

- 输出 token 数暴涨（思考 + 回答），Decode 时间成倍增长
- 需要把「思考过程」与「正式回答」分开返回
- 超时、并发、成本模型都要重新设计

---

## 2. 接口层：reasoning 字段

### OpenAI 风格（Responses API）

```python
from openai import OpenAI

client = OpenAI()

resp = client.responses.create(
    model="gpt-4.1-mini",
    input="证明：根号2 是无理数",
    reasoning={
        "effort": "medium",
        "summary": "auto",
    },
)

print(resp.output_text)
for item in resp.output:
    if item.type == "reasoning":
        print("思考片段:", item.summary)
```

### 开源模型（vLLM / SGLang 服务 DeepSeek-R1 / Qwen3）

```python
resp = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
    messages=[{"role": "user", "content": "证明：根号2 是无理数"}],
)

# 引擎会把思考内容放在 reasoning_content 字段
print(resp.choices[0].message.reasoning_content)
print(resp.choices[0].message.content)
```

> 不同引擎/版本对 reasoning 的支持程度不同；启动服务时确认对应参数（如 vLLM 的 `--enable-reasoning` 相关选项）与客户端字段，以官方文档为准。

---

## 3. 参数设计：思考预算

| 参数 | 作用 | 建议 |
|------|------|------|
| `max_tokens` | 思考 + 回答总上限 | 数学/推理题给足，如 16k+ |
| `reasoning_effort`（API 模型） | low/medium/high 思考强度 | 简单任务 low，难题 high |
| 预算强制（Budget Forcing） | 用 prompt/参数限制思考长度 | R1 蒸馏论文技术，开源模型可用 |
| `stop` / 温度 | 思考阶段特殊控制 | 按模型官方建议（R1 建议温度 0.6） |

### 预算强制的思想

```
限制思考 → 模型被迫更快收敛（省 token，牺牲部分准确率）
延长思考 → 「继续思考，不要结束」→ 更深入（花 token，换准确率）
```

生产上按题目难度动态分配预算，而不是一刀切。

---

## 4. 流式体验设计

思考过程可能 30 秒–数分钟，必须做流式：

```
用户看到：▋思考中…（可折叠）
           ▍ 2% → 45% → 92%
完成后：   [思考摘要]（可选展示）
           [正式回答]
```

实现建议：

- 前端先展示「思考中」状态，避免空白
- 思考与回答分两个流式阶段展示
- 提供跳过/取消按钮（高成本请求）
- 超时设置需远大于普通模型（按 90% 分位思考时长）

---

## 5. 成本与资源

思考型模型的成本公式：

```
单请求成本 ≈ (输入 tokens + 思考 tokens + 输出 tokens) × 单价
```

优化方向：

| 手段 | 效果 |
|------|------|
| effort 分级 | 低难度任务不付高思考费 |
| 答案缓存 | 相同问题直接复用 |
| 模型分级路由 | 简单→快模型，难题→思考模型 |
| 批量任务走离线 | 不占在线并发 |
| 前缀缓存 | RAG/Agent 提示词复用 |

---

## 6. 压测与监控特殊项

- 思考型请求输出长度方差极大 → 用「输出 token 分桶」看延迟
- 监控 `reasoning tokens / 总 tokens` 比例
- 关注长请求的流式断连率与超时率
- 并发设置建议比普通模型低（每个请求占用时间长）

---

## 7. 动手练习

1. 用任一支持思考的开源模型（如 Qwen3-8B 开 thinking 模式）启动服务
2. 分别设置 max_tokens=1024 / 4096，对比数学题回答质量与耗时
3. 实现一个「先展示思考进度，再展示回答」的流式前端逻辑（可仅打印两段内容）

---

## 8. 自检清单

- [ ] 能解释思考型模型对服务端的新挑战
- [ ] 能通过接口获取 reasoning 与正式回答
- [ ] 能设计思考预算与 effort 分级策略
- [ ] 能为思考型请求设计流式体验与超时
- [ ] 能估算思考型请求的成本构成

---

## 下一课

[`10-第10课生产部署 — DockerK8s弹性与成本.md`](<10-第10课生产部署 — DockerK8s弹性与成本.md>) — 生产部署、弹性与成本
