> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 监控与 MLOps

## 学习目标

- 掌握 AI 服务的监控体系
- 了解 MLOps 工具链（MLflow、Weights & Biases）
- 实现模型版本管理和自动化流水线

## 1. AI 服务监控

### 核心监控指标

```
性能指标：
- 响应延迟（P50/P95/P99）
- 吞吐量（QPS / tokens per second）
- 首 token 延迟（TTFT - Time To First Token）

资源指标：
- GPU 显存使用率
- GPU 利用率
- CPU/内存使用率
- 磁盘 I/O

业务指标：
- Token 消耗量
- API 调用次数
- 错误率
- 费用统计

质量指标：
- 用户满意度（点赞/点踩）
- 回答相关性
- 幻觉率
```

### Prometheus + Grafana

```python
# pip install prometheus-fastapi-instrumentator
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram, Gauge

# FastAPI 自动打点
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# 自定义指标
llm_request_count = Counter(
    'llm_request_total', 'Total LLM API calls',
    ['model', 'status']
)
llm_latency = Histogram(
    'llm_latency_seconds', 'LLM response latency',
    ['model'],
    buckets=[0.5, 1, 2, 5, 10, 30, 60]
)
llm_tokens = Counter(
    'llm_tokens_total', 'Total tokens consumed',
    ['model', 'type']  # type: prompt / completion
)
active_sessions = Gauge(
    'active_sessions', 'Number of active chat sessions'
)

# 在 LLM 调用时记录
import time

async def monitored_llm_call(messages, model="gpt-4o-mini"):
    start = time.time()
    try:
        response = await client.chat.completions.create(
            model=model, messages=messages
        )
        duration = time.time() - start

        llm_request_count.labels(model=model, status="success").inc()
        llm_latency.labels(model=model).observe(duration)
        llm_tokens.labels(model=model, type="prompt").inc(response.usage.prompt_tokens)
        llm_tokens.labels(model=model, type="completion").inc(response.usage.completion_tokens)

        return response
    except Exception as e:
        llm_request_count.labels(model=model, status="error").inc()
        raise
```

### Docker Compose 集成监控

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ai-service'
    static_configs:
      - targets: ['api:8000']
```

## 2. MLflow 实验管理

```bash
pip install mlflow
```

```python
import mlflow

# 启动 MLflow UI: mlflow ui --port 5000

# 记录微调实验
with mlflow.start_run(run_name="qwen-lora-finetune-v1"):
    # 记录参数
    mlflow.log_params({
        "base_model": "Qwen/Qwen2.5-7B-Instruct",
        "lora_r": 16,
        "lora_alpha": 32,
        "learning_rate": 2e-4,
        "epochs": 3,
        "dataset_size": 1000,
    })

    # 训练...

    # 记录指标
    mlflow.log_metrics({
        "train_loss": 0.35,
        "eval_loss": 0.42,
        "accuracy": 0.87,
        "f1_score": 0.85,
    })

    # 记录模型
    mlflow.log_artifacts("./lora-adapter", artifact_path="model")

    # 记录数据集信息
    mlflow.log_artifact("train.json", artifact_path="data")
```

### 模型注册与版本管理

```python
# 注册模型
model_uri = f"runs:/{run_id}/model"
mlflow.register_model(model_uri, "qa-assistant")

# 模型版本管理
client = mlflow.tracking.MlflowClient()

# 设置生产版本
client.transition_model_version_stage(
    name="qa-assistant",
    version=3,
    stage="Production",
)

# 加载生产模型
model = mlflow.pyfunc.load_model("models:/qa-assistant/Production")
```

## 3. 自动化评估流水线

```python
class EvaluationPipeline:
    """模型自动评估流水线"""

    def __init__(self, test_data_path: str):
        with open(test_data_path) as f:
            import json
            self.test_data = json.load(f)

    async def run(self, model_endpoint: str, model_name: str) -> dict:
        """运行完整评估"""
        from openai import AsyncOpenAI
        client = AsyncOpenAI(base_url=model_endpoint, api_key="token")

        results = {
            "model": model_name,
            "total": len(self.test_data),
            "scores": [],
            "latencies": [],
            "errors": 0,
        }

        for item in self.test_data:
            try:
                start = time.time()
                response = await client.chat.completions.create(
                    model=model_name,
                    messages=item["messages"][:-1],
                    max_tokens=500,
                )
                latency = time.time() - start

                generated = response.choices[0].message.content
                expected = item["messages"][-1]["content"]

                # 简单评估（实际应用中用更复杂的指标）
                score = 1 if any(kw in generated for kw in item.get("keywords", [])) else 0

                results["scores"].append(score)
                results["latencies"].append(latency)
            except Exception as e:
                results["errors"] += 1

        results["accuracy"] = sum(results["scores"]) / len(results["scores"]) if results["scores"] else 0
        results["avg_latency"] = sum(results["latencies"]) / len(results["latencies"]) if results["latencies"] else 0
        results["p95_latency"] = sorted(results["latencies"])[int(0.95 * len(results["latencies"]))] if results["latencies"] else 0

        return results
```

## 4. CI/CD for AI

```yaml
# .github/workflows/ai-deploy.yml
name: AI Service Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v

  evaluate:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run evaluation
        run: python evaluate.py --model gpt-4o-mini --threshold 0.85
      - name: Check results
        run: |
          if [ "$(cat eval_results.json | jq '.accuracy')" \< "0.85" ]; then
            echo "Evaluation failed: accuracy below threshold"
            exit 1
          fi

  deploy:
    needs: evaluate
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to server
        run: |
          ssh ${{ secrets.SERVER }} "cd /app && docker-compose pull && docker-compose up -d"
```

## 5. MLOps 成熟度模型

```
Level 0：手动实验
- Jupyter Notebook 实验
- 手动部署模型
- 无监控

Level 1：流程化
- 实验追踪（MLflow）
- Docker 容器化
- 基本监控

Level 2：自动化
- 自动评估流水线
- CI/CD 部署
- 完善的监控和告警

Level 3：持续优化
- A/B 测试
- 自动重训练
- 数据质量监控
- 模型性能漂移检测
```

## 练习

1. 为 AI 服务添加 Prometheus 监控指标
2. 用 MLflow 记录一次微调实验的完整信息
3. 实现一个自动化评估脚本，对比两个模型的性能
4. 编写 CI/CD 流水线，包含测试、评估、部署步骤

## 课程总结

恭喜你完成了 AI 开发专项课程的全部 12 个阶段！

### 你已掌握的技能树

```
🟢 基础篇
  ├── NumPy / Pandas / Matplotlib 数据科学生态
  ├── Scikit-learn 机器学习
  └── PyTorch 深度学习 + Transformer

🔵 大模型篇
  ├── LLM 原理 + Prompt Engineering
  ├── OpenAI API + Ollama + LangChain
  └── LoRA/QLoRA 微调

🟡 应用篇
  ├── 向量数据库 + Embedding
  ├── RAG 检索增强生成
  └── AI Agent + LangGraph

🔴 工程篇
  ├── 多模态 AI（视觉/语音/图像生成）
  ├── FastAPI AI 服务 + 架构模式
  └── Docker 部署 + MLOps 监控
```

### 下一步建议

1. **做项目**：选一个你感兴趣的领域，构建完整的 AI 应用
2. **读论文**：关注 arXiv 上的最新研究
3. **参与社区**：HuggingFace、GitHub 开源项目
4. **持续学习**：AI 领域发展极快，保持学习节奏
