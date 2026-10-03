import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第7课：完整项目 - 领域专家微调平台
==============================================================================

整合前6课知识，构建一个端到端的微调平台：

功能：
1. 数据管理（收集/清洗/增强/验证）
2. 训练管理（配置/启动/监控）
3. 评估管理（自动+LLM+人工）
4. 模型管理（版本/部署/切换）
5. 完整流水线

架构：
  数据准备 → 训练配置 → 训练执行 → 评估对比 → 模型部署
==============================================================================
"""

import json
import os
import time
import hashlib
import tempfile
import numpy as np
from datetime import datetime
from collections import defaultdict

import httpx

OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen2.5:7b"

print("=" * 60)
print("第7课：完整项目 - 领域专家微调平台")
print("=" * 60)

# ============================================================================
# 1. 数据管理模块
# ============================================================================
print("\n--- 1. 数据管理 ---")

class DataManager:
    """数据管理：收集/清洗/增强/验证"""

    def __init__(self):
        self.datasets = {}

    def create_from_qa(self, name: str, qa_pairs: list,
                       system_prompt: str) -> dict:
        data = []
        for qa in qa_pairs:
            data.append({"messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": qa["q"]},
                {"role": "assistant", "content": qa["a"]},
            ]})
        self.datasets[name] = data
        return {"name": name, "size": len(data)}

    def clean(self, name: str) -> dict:
        data = self.datasets.get(name, [])
        cleaned = []
        seen = set()
        removed = 0
        for item in data:
            msgs = item.get("messages", [])
            if len(msgs) < 2:
                removed += 1
                continue
            assistant = [m for m in msgs if m["role"] == "assistant"]
            if not assistant or len(assistant[0]["content"]) < 10:
                removed += 1
                continue
            h = hashlib.md5(json.dumps(msgs, ensure_ascii=False).encode()).hexdigest()
            if h in seen:
                removed += 1
                continue
            seen.add(h)
            cleaned.append(item)
        self.datasets[name] = cleaned
        return {"kept": len(cleaned), "removed": removed}

    def augment(self, name: str, topic: str, n: int = 5) -> dict:
        """LLM 数据增强"""
        try:
            resp = httpx.post(f"{OLLAMA_URL}/api/chat", json={
                "model": MODEL,
                "messages": [{"role": "user", "content":
                    f"为'{topic}'生成{n}个问答对，JSON数组：[{{\"q\":\"...\",\"a\":\"...\"}}]。只输出JSON。"}],
                "stream": False, "format": "json",
                "options": {"temperature": 0.7, "num_predict": 800}
            }, timeout=30.0)
            content = resp.json().get("message", {}).get("content", "[]")
            pairs = json.loads(content)
            if isinstance(pairs, dict):
                pairs = pairs.get("data", pairs.get("pairs", [pairs]))
            if not isinstance(pairs, list):
                pairs = [pairs]
        except:
            pairs = [{"q": f"关于{topic}的问题{i}", "a": f"关于{topic}的专业回答{i}"} for i in range(n)]

        system = ""
        if name in self.datasets and self.datasets[name]:
            first = self.datasets[name][0].get("messages", [])
            sys_msgs = [m for m in first if m["role"] == "system"]
            if sys_msgs:
                system = sys_msgs[0]["content"]

        for p in pairs[:n]:
            self.datasets.setdefault(name, []).append({"messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": str(p.get("q", ""))},
                {"role": "assistant", "content": str(p.get("a", ""))},
            ]})
        return {"generated": len(pairs[:n]), "total": len(self.datasets.get(name, []))}

    def split(self, name: str, val_ratio: float = 0.2) -> dict:
        data = self.datasets.get(name, [])
        np.random.seed(42)
        indices = np.random.permutation(len(data))
        split_idx = int(len(data) * (1 - val_ratio))
        train = [data[i] for i in indices[:split_idx]]
        val = [data[i] for i in indices[split_idx:]]
        self.datasets[f"{name}_train"] = train
        self.datasets[f"{name}_val"] = val
        return {"train": len(train), "val": len(val)}

    def validate(self, name: str) -> dict:
        data = self.datasets.get(name, [])
        errors = 0
        for item in data:
            msgs = item.get("messages", [])
            if not msgs or not any(m.get("role") == "assistant" for m in msgs):
                errors += 1
        return {"total": len(data), "errors": errors, "valid": errors == 0}

data_mgr = DataManager()

# 创建客服数据集
qa_data = [
    {"q": "退款需要多久？", "a": "退款通常在3-5个工作日内到账。如果超过5个工作日未收到退款，请联系我们的客服热线。"},
    {"q": "如何修改收货地址？", "a": "请登录您的账户，进入订单详情页面，点击'修改地址'按钮。如订单已发货，需联系快递公司协助修改。"},
    {"q": "能开发票吗？", "a": "当然可以。请在订单页面选择'申请发票'功能，我们支持电子发票和纸质发票两种形式。"},
    {"q": "会员有什么优惠？", "a": "会员享有以下专属权益：1.全场95折 2.包邮特权 3.优先客服通道 4.生日专属礼券 5.积分双倍。"},
    {"q": "商品质量有问题怎么办？", "a": "请在签收7天内发起退换货申请，拍照上传质量问题的照片，我们会在24小时内为您处理。"},
    {"q": "订单发货后多久能到？", "a": "普通快递3-5天到达，顺丰次日达（部分地区）。您可以在订单详情中查看物流实时信息。"},
    {"q": "如何使用优惠券？", "a": "结算时在优惠券栏目选择可用优惠券即可。注意优惠券有使用门槛和有效期限制。"},
    {"q": "支持哪些支付方式？", "a": "支持微信支付、支付宝、银行卡、花呗分期等多种支付方式。"},
]

result = data_mgr.create_from_qa("customer_service", qa_data, "你是一个专业的电商客服，回答简洁、友好、专业。")
print(f"创建数据集: {result}")

clean_result = data_mgr.clean("customer_service")
print(f"清洗: {clean_result}")

aug_result = data_mgr.augment("customer_service", "电商客服常见问题", 3)
print(f"增强: {aug_result}")

split_result = data_mgr.split("customer_service")
print(f"分割: {split_result}")

val_result = data_mgr.validate("customer_service_train")
print(f"验证: {val_result}")

# ============================================================================
# 2. 训练管理模块
# ============================================================================
print("\n--- 2. 训练管理 ---")

class TrainingManager:
    """训练管理：配置/模拟训练/监控"""

    def __init__(self):
        self.jobs = {}

    def create_config(self, name: str, base_model: str, method: str = "qlora",
                      **kwargs) -> dict:
        config = {
            "name": name, "base_model": base_model, "method": method,
            "r": kwargs.get("r", 16),
            "lora_alpha": kwargs.get("lora_alpha", 32),
            "target_modules": kwargs.get("target_modules",
                ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]),
            "epochs": kwargs.get("epochs", 3),
            "lr": kwargs.get("lr", 2e-4),
            "batch_size": kwargs.get("batch_size", 2),
            "grad_accum": kwargs.get("grad_accum", 4),
            "max_seq_length": kwargs.get("max_seq_length", 2048),
        }
        return config

    def start_training(self, config: dict, train_size: int) -> dict:
        job_id = f"job-{hash(config['name']) % 100000:05d}"
        np.random.seed(42)

        steps_per_epoch = train_size // (config["batch_size"] * config["grad_accum"])
        total_steps = steps_per_epoch * config["epochs"]

        logs = []
        loss = 2.5
        for step in range(1, total_steps + 1):
            progress = step / total_steps
            lr = config["lr"] * 0.5 * (1 + np.cos(np.pi * progress))
            loss = max(0.3, loss - 0.03 + np.random.normal(0, 0.015))
            eval_loss = loss + 0.08 + np.random.normal(0, 0.02)
            if step % max(1, total_steps // 8) == 0:
                logs.append({
                    "step": step, "epoch": round(step / steps_per_epoch, 1),
                    "train_loss": round(loss, 4),
                    "eval_loss": round(eval_loss, 4),
                    "lr": round(lr, 8),
                })

        job = {
            "id": job_id, "config": config, "status": "completed",
            "logs": logs, "train_size": train_size,
            "total_steps": total_steps,
            "final_loss": logs[-1]["train_loss"] if logs else 0,
            "adapter_path": f"./adapters/{config['name']}",
        }
        self.jobs[job_id] = job
        return job

train_mgr = TrainingManager()
config = train_mgr.create_config(
    "cs_expert_v1", "Qwen/Qwen2.5-7B-Instruct", "qlora",
    r=16, epochs=3, lr=2e-4
)
print(f"训练配置: {config['name']}")
print(f"  基座: {config['base_model']}")
print(f"  方法: {config['method']}, r={config['r']}")

job = train_mgr.start_training(config, split_result["train"])
print(f"\n训练完成:")
print(f"  Job: {job['id']}")
print(f"  步数: {job['total_steps']}")
print(f"  最终Loss: {job['final_loss']}")
print(f"  训练日志:")
for log in job["logs"]:
    print(f"    Step {log['step']:>3} | Epoch {log['epoch']:>4} | "
          f"Loss {log['train_loss']:.4f} | Eval {log['eval_loss']:.4f}")

# ============================================================================
# 3. 评估管理模块
# ============================================================================
print("\n--- 3. 评估管理 ---")

class EvaluationManager:
    """评估管理"""

    def __init__(self):
        self.reports = {}

    def evaluate(self, model_name: str, test_data: list) -> dict:
        """模拟评估"""
        np.random.seed(hash(model_name) % 2**31)
        results = []
        for item in test_data:
            user_msg = next((m["content"] for m in item["messages"] if m["role"] == "user"), "")
            ref_msg = next((m["content"] for m in item["messages"] if m["role"] == "assistant"), "")

            # 模拟模型输出（微调后更接近参考答案）
            if "微调" in model_name or "v1" in model_name:
                accuracy = np.random.uniform(0.7, 1.0)
                completeness = np.random.uniform(0.7, 1.0)
                style = np.random.uniform(0.8, 1.0)
            else:
                accuracy = np.random.uniform(0.4, 0.8)
                completeness = np.random.uniform(0.3, 0.7)
                style = np.random.uniform(0.3, 0.7)

            results.append({
                "question": user_msg[:30],
                "accuracy": round(accuracy * 5, 1),
                "completeness": round(completeness * 5, 1),
                "style": round(style * 5, 1),
                "total": round((accuracy + completeness + style) / 3 * 5, 1),
            })

        avg_total = np.mean([r["total"] for r in results])
        report = {
            "model": model_name,
            "test_size": len(test_data),
            "avg_score": round(avg_total, 2),
            "avg_accuracy": round(np.mean([r["accuracy"] for r in results]), 2),
            "avg_completeness": round(np.mean([r["completeness"] for r in results]), 2),
            "avg_style": round(np.mean([r["style"] for r in results]), 2),
            "details": results,
        }
        self.reports[model_name] = report
        return report

    def compare(self, model_a: str, model_b: str) -> dict:
        ra = self.reports.get(model_a, {})
        rb = self.reports.get(model_b, {})
        if not ra or not rb:
            return {"error": "模型未评估"}

        improvement = {
            "score": ra["avg_score"] - rb["avg_score"],
            "accuracy": ra["avg_accuracy"] - rb["avg_accuracy"],
            "completeness": ra["avg_completeness"] - rb["avg_completeness"],
            "style": ra["avg_style"] - rb["avg_style"],
        }
        return {
            "model_a": model_a, "model_b": model_b,
            "a_score": ra["avg_score"], "b_score": rb["avg_score"],
            "improvement": improvement,
            "winner": model_a if ra["avg_score"] > rb["avg_score"] else model_b,
        }

eval_mgr = EvaluationManager()
val_data = data_mgr.datasets.get("customer_service_val", [])

report_before = eval_mgr.evaluate("基座模型", val_data)
report_after = eval_mgr.evaluate("cs_expert_v1(微调)", val_data)

print(f"评估结果:")
print(f"  {'模型':<20} {'总分':>6} {'准确':>6} {'完整':>6} {'风格':>6}")
print(f"  {'-'*50}")
for r in [report_before, report_after]:
    print(f"  {r['model']:<20} {r['avg_score']:>5.1f} {r['avg_accuracy']:>5.1f} "
          f"{r['avg_completeness']:>5.1f} {r['avg_style']:>5.1f}")

comp = eval_mgr.compare("cs_expert_v1(微调)", "基座模型")
print(f"\n  对比: {comp['winner']} 更好")
print(f"  提升: 总分+{comp['improvement']['score']:.1f}, "
      f"准确+{comp['improvement']['accuracy']:.1f}, "
      f"风格+{comp['improvement']['style']:.1f}")

# ============================================================================
# 4. 模型管理模块
# ============================================================================
print("\n--- 4. 模型管理 ---")

class ModelManager:
    """模型版本管理"""

    def __init__(self):
        self.models = {}

    def register(self, name: str, base_model: str, adapter_path: str,
                 eval_score: float, config: dict) -> dict:
        version = f"v{len([k for k in self.models if k.startswith(name)]) + 1}"
        key = f"{name}_{version}"
        self.models[key] = {
            "name": name, "version": version,
            "base_model": base_model, "adapter_path": adapter_path,
            "eval_score": eval_score, "config": config,
            "created": datetime.now().isoformat(),
            "status": "ready",
        }
        return self.models[key]

    def get_best(self, name: str) -> dict:
        candidates = {k: v for k, v in self.models.items() if k.startswith(name)}
        if not candidates:
            return {}
        return max(candidates.values(), key=lambda x: x["eval_score"])

    def list_models(self) -> list:
        return [{k: {kk: vv for kk, vv in v.items() if kk != "config"}}
                for k, v in self.models.items()]

model_mgr = ModelManager()
model_mgr.register("cs_expert", "Qwen2.5-7B", "./adapters/v1",
                    report_after["avg_score"], config)
model_mgr.register("cs_expert", "Qwen2.5-7B", "./adapters/v2",
                    report_after["avg_score"] + 0.2, config)

print("已注册模型:")
for m in model_mgr.list_models():
    for k, v in m.items():
        print(f"  {k}: score={v['eval_score']}, status={v['status']}")

best = model_mgr.get_best("cs_expert")
print(f"最佳模型: {best['name']}_{best['version']} (score={best['eval_score']})")

# ============================================================================
# 5. 完整流水线
# ============================================================================
print("\n--- 5. 完整流水线 ---")

class FineTuningPipeline:
    """端到端微调流水线"""

    def __init__(self):
        self.data_mgr = DataManager()
        self.train_mgr = TrainingManager()
        self.eval_mgr = EvaluationManager()
        self.model_mgr = ModelManager()

    def run(self, name: str, qa_data: list, system_prompt: str,
            base_model: str = "Qwen/Qwen2.5-7B-Instruct",
            verbose: bool = True) -> dict:
        results = {}

        # Step 1: 数据准备
        if verbose: print(f"\n  [1/5] 数据准备...")
        self.data_mgr.create_from_qa(name, qa_data, system_prompt)
        self.data_mgr.clean(name)
        split = self.data_mgr.split(name, val_ratio=0.2)
        val = self.data_mgr.validate(f"{name}_train")
        results["data"] = {"split": split, "valid": val["valid"]}
        if verbose: print(f"    训练: {split['train']}, 验证: {split['val']}")

        # Step 2: 训练配置
        if verbose: print(f"  [2/5] 训练配置...")
        config = self.train_mgr.create_config(name, base_model, "qlora")
        results["config"] = {"method": "qlora", "r": config["r"]}

        # Step 3: 训练
        if verbose: print(f"  [3/5] 训练...")
        job = self.train_mgr.start_training(config, split["train"])
        results["training"] = {"job_id": job["id"], "final_loss": job["final_loss"]}
        if verbose: print(f"    完成! Loss: {job['final_loss']}")

        # Step 4: 评估
        if verbose: print(f"  [4/5] 评估...")
        val_data = self.data_mgr.datasets.get(f"{name}_val", [])
        eval_before = self.eval_mgr.evaluate(f"{name}_base", val_data)
        eval_after = self.eval_mgr.evaluate(f"{name}_tuned", val_data)
        comp = self.eval_mgr.compare(f"{name}_tuned", f"{name}_base")
        results["evaluation"] = {
            "before": eval_before["avg_score"],
            "after": eval_after["avg_score"],
            "improvement": comp["improvement"]["score"],
        }
        if verbose: print(f"    基座: {eval_before['avg_score']:.1f} → 微调: {eval_after['avg_score']:.1f}")

        # Step 5: 注册模型
        if verbose: print(f"  [5/5] 注册模型...")
        model = self.model_mgr.register(
            name, base_model, job["adapter_path"],
            eval_after["avg_score"], config
        )
        results["model"] = {"version": model["version"], "score": model["eval_score"]}
        if verbose: print(f"    注册: {model['name']}_{model['version']}")

        return results

# 运行完整流水线
pipeline = FineTuningPipeline()
print("运行完整微调流水线:")
result = pipeline.run(
    name="medical_assistant",
    qa_data=[
        {"q": "感冒了怎么办？", "a": "建议多休息、多饮水。如果发烧超过38.5°C，可服用退烧药。症状持续3天以上请就医。"},
        {"q": "头痛常见原因？", "a": "常见原因包括：紧张性头痛、偏头痛、睡眠不足、颈椎问题等。频繁头痛建议做进一步检查。"},
        {"q": "血压正常范围？", "a": "成人正常血压：收缩压90-140mmHg，舒张压60-90mmHg。建议定期监测。"},
        {"q": "如何预防流感？", "a": "建议：1.接种流感疫苗 2.勤洗手 3.保持室内通风 4.增强免疫力 5.避免人群密集场所。"},
        {"q": "腰痛怎么缓解？", "a": "建议：1.避免久坐 2.适当运动(游泳/瑜伽) 3.热敷 4.保持正确坐姿。持续疼痛请就医。"},
    ],
    system_prompt="你是专业的医疗健康咨询助手。回答要专业、准确、适度谨慎。",
)

# ============================================================================
# 6. 项目架构总结
# ============================================================================
print(f"""
┌────────────────────────────────────────────────────────┐
│         领域专家微调平台 - 项目架构                      │
├────────────────────────────────────────────────────────┤
│                                                        │
│  FineTuningPipeline（主控流水线）                      │
│  └── run()  5步端到端流水线                            │
│                                                        │
│  DataManager（数据管理）                               │
│  ├── create_from_qa()    创建数据集                    │
│  ├── clean()             数据清洗                      │
│  ├── augment()           LLM数据增强                   │
│  ├── split()             训练/验证分割                 │
│  └── validate()          数据验证                      │
│                                                        │
│  TrainingManager（训练管理）                            │
│  ├── create_config()     训练配置                      │
│  └── start_training()    启动训练                      │
│                                                        │
│  EvaluationManager（评估管理）                         │
│  ├── evaluate()          模型评估                      │
│  └── compare()           A/B对比                       │
│                                                        │
│  ModelManager（模型管理）                               │
│  ├── register()          注册模型                      │
│  ├── get_best()          获取最佳版本                  │
│  └── list_models()       列出所有模型                  │
│                                                        │
│  整合的知识                                            │
│  ├── 第1课: 微调原理/方式对比/决策                    │
│  ├── 第2课: 数据格式/清洗/增强/验证                  │
│  ├── 第3课: LoRA/QLoRA原理/PEFT使用                  │
│  ├── 第4课: SFTTrainer/超参数/监控                    │
│  ├── 第5课: OpenAI FT API/云端微调                    │
│  └── 第6课: 评估体系/LLM-Judge/A/B测试              │
│                                                        │
│  扩展方向                                              │
│  → Web UI（训练任务管理界面）                          │
│  → 真实 GPU 训练（HF/Unsloth）                        │
│  → 自动超参搜索（Optuna）                             │
│  → 模型导出（GGUF→Ollama 部署）                       │
│  → 持续微调（新数据自动触发）                         │
│  → 多模型 A/B 线上测试                                │
└────────────────────────────────────────────────────────┘
""")

print("=" * 60)
print("[完成] 第7课完成！你已经学会了：")
print("  [v] 数据管理（收集/清洗/增强/分割/验证）")
print("  [v] 训练管理（配置/执行/监控）")
print("  [v] 评估管理（自动/LLM/对比）")
print("  [v] 模型管理（版本/注册/最佳选择）")
print("  [v] 端到端微调流水线")
print("  [v] 整合前6课全部核心知识")
print("=" * 60)
print("\nlearn-fine-tuning 课程全部完成！🎉")
