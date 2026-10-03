import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第6课：MLflow 实验管理与 CI/CD
==============================================================================

MLflow = AI 实验追踪 + 模型版本管理
CI/CD = 自动化测试 + 评估 + 部署

本课内容：
1. MLflow 概述
2. 实验追踪
3. 模型注册与版本
4. CI/CD for AI
5. 自动化评估
6. MLOps 成熟度
==============================================================================
"""

import json
import time
import hashlib
from datetime import datetime
from collections import OrderedDict

print("=" * 60)
print("第6课：MLflow 与 CI/CD")
print("=" * 60)

# ============================================================================
# 1. MLflow 概述
# ============================================================================
print("\n--- 1. MLflow ---")
print("""
MLflow 四大组件：

┌──────────────────┬──────────────────────────────────────┐
│  Tracking        │  记录实验参数、指标、产物             │
│                  │  对比不同实验结果                     │
├──────────────────┼──────────────────────────────────────┤
│  Models          │  统一模型格式，支持多框架             │
│                  │  模型打包和部署                       │
├──────────────────┼──────────────────────────────────────┤
│  Model Registry  │  模型版本管理                         │
│                  │  Staging → Production 生命周期        │
├──────────────────┼──────────────────────────────────────┤
│  Projects        │  可复现的实验环境                     │
│                  │  MLproject 文件定义                   │
└──────────────────┴──────────────────────────────────────┘

安装和启动：
```bash
pip install mlflow
mlflow ui --port 5000
# 访问 http://localhost:5000
```
""")

# ============================================================================
# 2. 实验追踪
# ============================================================================
print("\n--- 2. 实验追踪 ---")

class ExperimentTracker:
    """实验追踪器（模拟 MLflow Tracking）"""

    def __init__(self):
        self.experiments = {}
        self.runs = {}

    def create_experiment(self, name: str) -> str:
        exp_id = hashlib.md5(name.encode()).hexdigest()[:8]
        self.experiments[exp_id] = {"name": name, "runs": []}
        return exp_id

    def start_run(self, experiment_id: str, run_name: str) -> str:
        run_id = hashlib.md5(f"{run_name}{time.time()}".encode()).hexdigest()[:8]
        self.runs[run_id] = {
            "run_name": run_name,
            "experiment_id": experiment_id,
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "params": {},
            "metrics": {},
            "artifacts": [],
            "tags": {},
        }
        self.experiments[experiment_id]["runs"].append(run_id)
        return run_id

    def log_params(self, run_id: str, params: dict):
        self.runs[run_id]["params"].update(params)

    def log_metrics(self, run_id: str, metrics: dict):
        self.runs[run_id]["metrics"].update(metrics)

    def log_artifact(self, run_id: str, artifact_path: str):
        self.runs[run_id]["artifacts"].append(artifact_path)

    def set_tag(self, run_id: str, key: str, value: str):
        self.runs[run_id]["tags"][key] = value

    def end_run(self, run_id: str, status: str = "finished"):
        self.runs[run_id]["status"] = status
        self.runs[run_id]["end_time"] = datetime.now().isoformat()

    def compare_runs(self, run_ids: list) -> list:
        results = []
        for rid in run_ids:
            run = self.runs[rid]
            results.append({
                "run_id": rid,
                "name": run["run_name"],
                "params": run["params"],
                "metrics": run["metrics"],
            })
        return results

tracker = ExperimentTracker()

# 创建实验
exp_id = tracker.create_experiment("QA-Assistant-FineTuning")
print(f"实验: QA-Assistant-FineTuning (id={exp_id})")

# 运行1: LoRA 微调
run1 = tracker.start_run(exp_id, "lora-r16-lr2e4")
tracker.log_params(run1, {
    "base_model": "Qwen/Qwen2.5-7B-Instruct",
    "method": "LoRA",
    "lora_r": 16, "lora_alpha": 32,
    "learning_rate": 2e-4, "epochs": 3,
    "dataset_size": 1000,
})
tracker.log_metrics(run1, {
    "train_loss": 0.35, "eval_loss": 0.42,
    "accuracy": 0.87, "f1_score": 0.85,
    "latency_ms": 850,
})
tracker.log_artifact(run1, "lora-adapter/")
tracker.set_tag(run1, "model_type", "lora")
tracker.end_run(run1)

# 运行2: QLoRA 微调
run2 = tracker.start_run(exp_id, "qlora-r8-lr1e4")
tracker.log_params(run2, {
    "base_model": "Qwen/Qwen2.5-7B-Instruct",
    "method": "QLoRA",
    "lora_r": 8, "lora_alpha": 16,
    "learning_rate": 1e-4, "epochs": 5,
    "dataset_size": 1000,
})
tracker.log_metrics(run2, {
    "train_loss": 0.32, "eval_loss": 0.39,
    "accuracy": 0.89, "f1_score": 0.87,
    "latency_ms": 820,
})
tracker.log_artifact(run2, "qlora-adapter/")
tracker.set_tag(run2, "model_type", "qlora")
tracker.end_run(run2)

# 运行3: 全量微调
run3 = tracker.start_run(exp_id, "full-ft-lr5e5")
tracker.log_params(run3, {
    "base_model": "Qwen/Qwen2.5-7B-Instruct",
    "method": "Full",
    "learning_rate": 5e-5, "epochs": 2,
    "dataset_size": 1000,
})
tracker.log_metrics(run3, {
    "train_loss": 0.28, "eval_loss": 0.45,
    "accuracy": 0.86, "f1_score": 0.84,
    "latency_ms": 900,
})
tracker.end_run(run3)

# 对比实验
comparison = tracker.compare_runs([run1, run2, run3])
print(f"\n实验对比:")
print(f"  {'运行名':<20} {'方法':<8} {'准确率':>8} {'F1':>8} {'延迟(ms)':>10}")
print(f"  {'-'*56}")
for r in comparison:
    print(f"  {r['name']:<20} {r['params'].get('method',''):<8} "
          f"{r['metrics'].get('accuracy',0):>7.2f} "
          f"{r['metrics'].get('f1_score',0):>7.2f} "
          f"{r['metrics'].get('latency_ms',0):>10}")

print("""
MLflow Tracking 实际使用：
```python
import mlflow

mlflow.set_experiment("QA-Assistant")

with mlflow.start_run(run_name="lora-v1"):
    mlflow.log_params({"lora_r": 16, "lr": 2e-4})
    # ... 训练 ...
    mlflow.log_metrics({"accuracy": 0.87, "f1": 0.85})
    mlflow.log_artifacts("./lora-adapter", "model")
```
""")

# ============================================================================
# 3. 模型注册
# ============================================================================
print("\n--- 3. 模型注册 ---")

class ModelRegistry:
    """模型注册表（模拟 MLflow Model Registry）"""

    def __init__(self):
        self.models = {}

    def register(self, name: str, run_id: str, description: str = "") -> dict:
        if name not in self.models:
            self.models[name] = {"versions": [], "description": description}
        version = len(self.models[name]["versions"]) + 1
        entry = {
            "version": version,
            "run_id": run_id,
            "stage": "None",
            "created": datetime.now().isoformat(),
        }
        self.models[name]["versions"].append(entry)
        return entry

    def transition_stage(self, name: str, version: int, stage: str):
        """转换模型阶段: None → Staging → Production → Archived"""
        versions = self.models[name]["versions"]
        # 如果是 Production，先把当前 Production 归档
        if stage == "Production":
            for v in versions:
                if v["stage"] == "Production":
                    v["stage"] = "Archived"
        versions[version - 1]["stage"] = stage

    def get_production(self, name: str) -> dict:
        for v in self.models[name]["versions"]:
            if v["stage"] == "Production":
                return v
        return None

    def list_versions(self, name: str) -> list:
        return self.models.get(name, {}).get("versions", [])

registry = ModelRegistry()

# 注册模型版本
v1 = registry.register("qa-assistant", run1, "QA问答助手")
v2 = registry.register("qa-assistant", run2)
v3 = registry.register("qa-assistant", run3)

# 生命周期管理
registry.transition_stage("qa-assistant", 1, "Staging")
registry.transition_stage("qa-assistant", 2, "Production")
registry.transition_stage("qa-assistant", 1, "Archived")

print(f"模型版本:")
for v in registry.list_versions("qa-assistant"):
    print(f"  v{v['version']}: run={v['run_id']}, stage={v['stage']}")

prod = registry.get_production("qa-assistant")
print(f"当前生产版本: v{prod['version']} (run={prod['run_id']})")

print("""
模型生命周期：
  None → Staging → Production → Archived
           ↑          │
           └──────────┘  （回滚）

MLflow 实际使用：
```python
# 注册
mlflow.register_model(f"runs:/{run_id}/model", "qa-assistant")

# 升级到生产
client = mlflow.tracking.MlflowClient()
client.transition_model_version_stage("qa-assistant", 2, "Production")

# 加载生产模型
model = mlflow.pyfunc.load_model("models:/qa-assistant/Production")
```
""")

# ============================================================================
# 4. CI/CD for AI
# ============================================================================
print("\n--- 4. CI/CD ---")
print("""
AI 服务 CI/CD 流水线：

  Push Code → Test → Evaluate → Build → Deploy
      │         │        │         │        │
      │      单元测试  模型评估  Docker镜像 滚动部署
      │      集成测试  A/B测试   推送Registry
      │      Lint      质量门禁
      │
  GitHub / GitLab

GitHub Actions 示例：
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
        with: { python-version: '3.11' }
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v

  evaluate:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run evaluation
        run: python evaluate.py --threshold 0.85
      - name: Quality gate
        run: |
          score=$(cat eval_results.json | python -c "import sys,json;print(json.load(sys.stdin)['accuracy'])")
          if (( $(echo "$score < 0.85" | bc -l) )); then
            echo "质量门禁未通过: $score < 0.85"
            exit 1
          fi

  deploy:
    needs: evaluate
    runs-on: ubuntu-latest
    steps:
      - name: Build and push Docker image
        run: |
          docker build -t myregistry/ai-service:${{ github.sha }} .
          docker push myregistry/ai-service:${{ github.sha }}
      - name: Deploy
        run: |
          ssh ${{ secrets.SERVER }} \\
            "cd /app && docker-compose pull && docker-compose up -d"
```
""")

# ============================================================================
# 5. 自动化评估
# ============================================================================
print("\n--- 5. 自动评估 ---")

class EvaluationPipeline:
    """自动化评估流水线"""

    def __init__(self, test_cases: list):
        self.test_cases = test_cases

    def evaluate(self, model_fn) -> dict:
        """运行评估"""
        results = {
            "total": len(self.test_cases),
            "correct": 0,
            "latencies": [],
            "errors": 0,
        }

        for case in self.test_cases:
            try:
                start = time.time()
                answer = model_fn(case["question"])
                latency = time.time() - start

                # 关键词匹配评估
                hit = any(kw.lower() in answer.lower()
                          for kw in case.get("keywords", []))
                if hit:
                    results["correct"] += 1
                results["latencies"].append(latency)
            except Exception as e:
                results["errors"] += 1

        import numpy as np
        lats = np.array(results["latencies"]) if results["latencies"] else np.array([0])
        results["accuracy"] = results["correct"] / results["total"] if results["total"] else 0
        results["avg_latency"] = round(float(np.mean(lats)), 3)
        results["p95_latency"] = round(float(np.percentile(lats, 95)), 3)

        return results

    def quality_gate(self, results: dict,
                     min_accuracy: float = 0.85,
                     max_p95_latency: float = 5.0) -> dict:
        """质量门禁"""
        passed = True
        checks = []

        if results["accuracy"] < min_accuracy:
            passed = False
            checks.append(f"准确率 {results['accuracy']:.2f} < {min_accuracy}")
        else:
            checks.append(f"准确率 {results['accuracy']:.2f} >= {min_accuracy} ✓")

        if results["p95_latency"] > max_p95_latency:
            passed = False
            checks.append(f"P95延迟 {results['p95_latency']:.2f}s > {max_p95_latency}s")
        else:
            checks.append(f"P95延迟 {results['p95_latency']:.2f}s <= {max_p95_latency}s ✓")

        if results["errors"] > 0:
            checks.append(f"错误: {results['errors']} 次 ⚠")

        return {"passed": passed, "checks": checks}

# 测试用例
test_cases = [
    {"question": "什么是RAG？", "keywords": ["检索", "生成", "retrieval"]},
    {"question": "LoRA 的原理是什么？", "keywords": ["低秩", "矩阵", "参数"]},
    {"question": "Docker 有什么优势？", "keywords": ["容器", "隔离", "部署"]},
    {"question": "vLLM 的核心技术？", "keywords": ["paged", "attention", "批处理"]},
    {"question": "Prompt 注入怎么防御？", "keywords": ["检测", "过滤", "安全"]},
]

pipeline = EvaluationPipeline(test_cases)

# 模拟模型回答
def mock_model(question):
    answers = {
        "RAG": "RAG是检索增强生成技术，通过检索外部文档辅助LLM生成",
        "LoRA": "LoRA通过低秩矩阵分解减少微调参数量",
        "Docker": "Docker将应用容器化，实现环境隔离和快速部署",
        "vLLM": "vLLM使用PagedAttention优化KV Cache，支持连续批处理",
        "Prompt": "通过输入检测和过滤规则防御Prompt注入，确保安全",
    }
    for key, answer in answers.items():
        if key in question:
            time.sleep(0.01)
            return answer
    return "抱歉，我不知道。"

results = pipeline.evaluate(mock_model)
gate = pipeline.quality_gate(results)

print(f"评估结果:")
print(f"  总数: {results['total']}, 正确: {results['correct']}, 错误: {results['errors']}")
print(f"  准确率: {results['accuracy']:.2f}")
print(f"  平均延迟: {results['avg_latency']}s, P95: {results['p95_latency']}s")
print(f"\n质量门禁: {'✓ 通过' if gate['passed'] else '✗ 未通过'}")
for check in gate["checks"]:
    print(f"  {check}")

# ============================================================================
# 6. MLOps 成熟度
# ============================================================================
print("\n--- 6. 成熟度 ---")
print("""
MLOps 成熟度模型：

Level 0: 手动实验
  □ Jupyter Notebook 实验
  □ 手动复制模型到服务器
  □ 无监控，出问题靠用户反馈

Level 1: 流程化
  ✓ MLflow 实验追踪
  ✓ Docker 容器化部署
  ✓ 基本监控（延迟/错误率）
  □ 手动触发部署

Level 2: 自动化
  ✓ CI/CD 自动部署
  ✓ 自动化评估流水线
  ✓ 质量门禁（评估不过不部署）
  ✓ 完善的监控和告警
  □ 模型更新仍需手动触发

Level 3: 持续优化
  ✓ A/B 测试（灰度发布）
  ✓ 自动重训练（数据更新触发）
  ✓ 数据质量监控
  ✓ 模型性能漂移检测
  ✓ 自动回滚

推荐目标：Level 2
  满足 90% 的生产需求
  投入产出比最高
""")

print("=" * 60)
print("[完成] 第6课完成！你已经学会了：")
print("  [v] MLflow 实验追踪（参数/指标/产物）")
print("  [v] 模型注册与版本管理")
print("  [v] CI/CD 流水线（测试→评估→部署）")
print("  [v] 自动化评估与质量门禁")
print("  [v] MLOps 成熟度模型")
print("=" * 60)
print("\n下一课：07_mlops_project.py - AI 运维平台项目")
