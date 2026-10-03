import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第7课：完整项目 - 自动化 Prompt 工程平台
==============================================================================

整合前6课知识，构建一个 Prompt 工程平台：

功能：
1. Prompt 模板管理（CRUD + 版本）
2. 变量填充与批量执行
3. A/B 测试与评估
4. 自动优化（元提示）
5. 成本追踪
6. 管道编排

架构：
  模板库 → 填充 → 执行 → 评估 → 优化 → 版本管理
==============================================================================
"""

import json
import time
import hashlib
from datetime import datetime
from collections import defaultdict

import httpx

OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen2.5:7b"

print("=" * 60)
print("第7课：完整项目 - Prompt 工程平台")
print("=" * 60)

# ============================================================================
# 1. LLM 调用层
# ============================================================================
print("\n--- 1. LLM 调用层 ---")

class LLMClient:
    """统一的 LLM 调用客户端"""

    def __init__(self, model: str = MODEL):
        self.model = model
        self.call_log = []
        self.cache = {}

    def chat(self, messages: list, temperature: float = 0.3,
             max_tokens: int = 500, use_cache: bool = True) -> dict:
        cache_key = hashlib.md5(json.dumps(messages, ensure_ascii=False).encode()).hexdigest()

        if use_cache and cache_key in self.cache:
            return {**self.cache[cache_key], "cached": True}

        start = time.time()
        try:
            resp = httpx.post(f"{OLLAMA_URL}/api/chat", json={
                "model": self.model, "messages": messages, "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens}
            }, timeout=30.0)
            content = resp.json().get("message", {}).get("content", "")
        except:
            content = f"[模拟回答] 针对输入的回复"

        elapsed = int((time.time() - start) * 1000)
        result = {
            "content": content, "latency_ms": elapsed,
            "model": self.model, "cached": False,
            "input_chars": sum(len(m["content"]) for m in messages),
            "output_chars": len(content),
        }

        self.cache[cache_key] = result
        self.call_log.append({**result, "timestamp": datetime.now().isoformat()})
        return result

    def get_stats(self) -> dict:
        if not self.call_log:
            return {"total_calls": 0}
        return {
            "total_calls": len(self.call_log),
            "cached_calls": sum(1 for c in self.call_log if c.get("cached")),
            "avg_latency": sum(c["latency_ms"] for c in self.call_log) / len(self.call_log),
            "total_input_chars": sum(c["input_chars"] for c in self.call_log),
            "total_output_chars": sum(c["output_chars"] for c in self.call_log),
        }

llm = LLMClient()
print(f"LLM 客户端: model={llm.model}, 缓存=✓")

# ============================================================================
# 2. Prompt 模板管理
# ============================================================================
print("\n--- 2. 模板管理 ---")

class PromptTemplate:
    """Prompt 模板"""

    def __init__(self, name: str, system: str, template: str,
                 version: str = "1.0", temperature: float = 0.3,
                 max_tokens: int = 500, tags: list = None):
        self.name = name
        self.system = system
        self.template = template
        self.version = version
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.tags = tags or []
        self.created = datetime.now().isoformat()

    def fill(self, **kwargs) -> str:
        result = self.template
        for key, val in kwargs.items():
            result = result.replace(f"{{{key}}}", str(val))
        return result

    def to_messages(self, **kwargs) -> list:
        messages = []
        if self.system:
            messages.append({"role": "system", "content": self.system})
        messages.append({"role": "user", "content": self.fill(**kwargs)})
        return messages

    def execute(self, client: LLMClient, **kwargs) -> dict:
        messages = self.to_messages(**kwargs)
        return client.chat(messages, self.temperature, self.max_tokens)

    def to_dict(self) -> dict:
        return {
            "name": self.name, "version": self.version,
            "system": self.system[:50], "template": self.template[:50],
            "temperature": self.temperature, "tags": self.tags,
        }

class TemplateRegistry:
    """模板注册表"""

    def __init__(self):
        self.templates = {}

    def register(self, template: PromptTemplate):
        key = f"{template.name}@{template.version}"
        self.templates[key] = template
        return key

    def get(self, name: str, version: str = None) -> PromptTemplate:
        if version:
            return self.templates.get(f"{name}@{version}")
        matches = [(k, v) for k, v in self.templates.items() if k.startswith(f"{name}@")]
        return matches[-1][1] if matches else None

    def list_all(self) -> list:
        return [t.to_dict() for t in self.templates.values()]

registry = TemplateRegistry()

# 注册模板
templates = [
    PromptTemplate("sentiment", "你是情感分析专家，只输出JSON。",
                   '分析评论情感，输出：{{"sentiment":"positive/negative/neutral","confidence":0.0-1.0}}\n评论：{text}',
                   version="1.0", temperature=0.0, tags=["nlp", "classification"]),
    PromptTemplate("translate", "你是专业翻译官，中英互译。翻译自然流畅，保留专业术语原文。",
                   "翻译以下文本（自动判断翻译方向）：\n{text}\n只输出翻译结果。",
                   version="1.0", temperature=0.3, tags=["nlp", "translation"]),
    PromptTemplate("summarize", "你是摘要专家。",
                   "将以下文本总结为{length}字以内的摘要：\n{text}",
                   version="1.0", temperature=0.3, tags=["nlp", "summarization"]),
    PromptTemplate("code_review", "你是资深代码审查专家。",
                   "审查以下{language}代码，列出问题和建议：\n```{language}\n{code}\n```\n格式：🔴严重 🟡建议 🟢优点",
                   version="1.0", temperature=0.3, tags=["code", "review"]),
    PromptTemplate("extract", "你是数据提取专家，只输出JSON。",
                   "从以下文本中提取{fields}，输出JSON。\n文本：{text}",
                   version="1.0", temperature=0.0, tags=["nlp", "extraction"]),
]

for t in templates:
    registry.register(t)

print(f"已注册 {len(registry.templates)} 个模板:")
for t in registry.list_all():
    print(f"  {t['name']}@{t['version']} [{','.join(t['tags'])}]")

# ============================================================================
# 3. 批量执行
# ============================================================================
print("\n--- 3. 批量执行 ---")

class BatchExecutor:
    """批量执行引擎"""

    def __init__(self, client: LLMClient):
        self.client = client

    def execute_batch(self, template: PromptTemplate,
                      inputs: list, verbose: bool = True) -> list:
        results = []
        for i, params in enumerate(inputs):
            result = template.execute(self.client, **params)
            results.append({**params, "output": result["content"],
                            "latency": result["latency_ms"]})
            if verbose:
                first_key = list(params.keys())[0]
                print(f"    [{i+1}/{len(inputs)}] {params[first_key][:30]}... → "
                      f"{result['content'][:40]}... ({result['latency_ms']}ms)")
        return results

executor = BatchExecutor(llm)

# 批量情感分析
sentiment_template = registry.get("sentiment")
test_inputs = [
    {"text": "这款手机拍照效果太棒了！"},
    {"text": "售后服务态度很差，再也不买了"},
    {"text": "产品中规中矩，没什么特别的"},
    {"text": "包装精美，但功能不如预期"},
]

print("批量情感分析:")
results = executor.execute_batch(sentiment_template, test_inputs)

# ============================================================================
# 4. A/B 测试与评估
# ============================================================================
print("\n--- 4. A/B 测试 ---")

class ABTester:
    """A/B 测试引擎"""

    def __init__(self, client: LLMClient):
        self.client = client
        self.reports = []

    def test(self, template_a: PromptTemplate, template_b: PromptTemplate,
             test_cases: list, judge_criteria: str = "") -> dict:
        """对比两个模板"""
        scores_a = {"total": 0, "format_ok": 0, "latency": 0}
        scores_b = {"total": 0, "format_ok": 0, "latency": 0}

        for tc in test_cases:
            # 执行 A
            ra = template_a.execute(self.client, **tc)
            scores_a["total"] += 1
            scores_a["latency"] += ra["latency_ms"]
            try:
                json.loads(ra["content"].strip().strip("`").replace("json\n", ""))
                scores_a["format_ok"] += 1
            except:
                s, e = ra["content"].find("{"), ra["content"].rfind("}")
                if s != -1 and e != -1:
                    try:
                        json.loads(ra["content"][s:e+1])
                        scores_a["format_ok"] += 1
                    except:
                        pass

            # 执行 B
            rb = template_b.execute(self.client, **tc)
            scores_b["total"] += 1
            scores_b["latency"] += rb["latency_ms"]
            try:
                json.loads(rb["content"].strip().strip("`").replace("json\n", ""))
                scores_b["format_ok"] += 1
            except:
                s, e = rb["content"].find("{"), rb["content"].rfind("}")
                if s != -1 and e != -1:
                    try:
                        json.loads(rb["content"][s:e+1])
                        scores_b["format_ok"] += 1
                    except:
                        pass

        n = len(test_cases)
        report = {
            "A": {"name": template_a.name + "@" + template_a.version,
                   "format_rate": scores_a["format_ok"] / n,
                   "avg_latency": scores_a["latency"] / n},
            "B": {"name": template_b.name + "@" + template_b.version,
                   "format_rate": scores_b["format_ok"] / n,
                   "avg_latency": scores_b["latency"] / n},
            "winner": "A" if scores_a["format_ok"] >= scores_b["format_ok"] else "B",
        }
        self.reports.append(report)
        return report

# 创建 v2 情感模板
sentiment_v2 = PromptTemplate(
    "sentiment", "你是情感分析专家。",
    '判断情感。\n示例："好吃"→{{"sentiment":"positive","confidence":0.9}}\n"太差"→{{"sentiment":"negative","confidence":0.9}}\n\n评论：{text}\nJSON：',
    version="2.0", temperature=0.0, tags=["nlp"]
)
registry.register(sentiment_v2)

tester = ABTester(llm)
ab_cases = [{"text": t["text"]} for t in test_inputs]
report = tester.test(sentiment_template, sentiment_v2, ab_cases)

print(f"A/B 测试结果:")
print(f"  A ({report['A']['name']}): 格式率={report['A']['format_rate']:.0%}, 延迟={report['A']['avg_latency']:.0f}ms")
print(f"  B ({report['B']['name']}): 格式率={report['B']['format_rate']:.0%}, 延迟={report['B']['avg_latency']:.0f}ms")
print(f"  胜者: {report['winner']}")

# ============================================================================
# 5. 管道编排
# ============================================================================
print("\n--- 5. 管道编排 ---")

class Pipeline:
    """多步 Prompt 管道"""

    def __init__(self, name: str, client: LLMClient):
        self.name = name
        self.client = client
        self.steps = []

    def add_step(self, step_name: str, template: PromptTemplate,
                 input_mapping: dict = None):
        self.steps.append({
            "name": step_name, "template": template,
            "mapping": input_mapping or {}
        })

    def run(self, initial_input: dict, verbose: bool = True) -> dict:
        context = {**initial_input}
        step_results = []

        for step in self.steps:
            params = {}
            for tpl_var, source in step["mapping"].items():
                if source in context:
                    params[tpl_var] = context[source]
                elif source in initial_input:
                    params[tpl_var] = initial_input[source]

            # 未映射的变量从 context 取
            for key, val in context.items():
                if key not in params:
                    params[key] = val

            result = step["template"].execute(self.client, **params)
            context[f"step_{step['name']}"] = result["content"]
            context["text"] = result["content"]  # 默认传递

            step_results.append({
                "step": step["name"],
                "output": result["content"][:80],
                "latency": result["latency_ms"],
            })

            if verbose:
                print(f"    [{step['name']}] {result['content'][:60]}... ({result['latency_ms']}ms)")

        return {"steps": step_results, "final": context.get("text", "")}

# 构建文章处理管道
extract_tpl = PromptTemplate("pipe_extract", "", "提取以下文本的关键信息（人物/事件/数据），用要点列出：\n{text}", temperature=0.3)
summarize_tpl = PromptTemplate("pipe_summarize", "", "将以下要点写成50字以内的摘要：\n{text}", temperature=0.3)

pipe = Pipeline("article_processor", llm)
pipe.add_step("extract", extract_tpl)
pipe.add_step("summarize", summarize_tpl)

print("文章处理管道:")
article = "2024年，OpenAI发布GPT-4o，这是首个原生多模态模型。同年Google发布Gemini 1.5 Pro，支持100万token上下文。Meta开源LLaMA 3，推动开源AI发展。"
result = pipe.run({"text": article})

# ============================================================================
# 6. 平台统计
# ============================================================================
print("\n--- 6. 平台统计 ---")

stats = llm.get_stats()
print(f"""
┌────────────────────────────────────────────────────────┐
│         Prompt 工程平台 - 项目架构                      │
├────────────────────────────────────────────────────────┤
│                                                        │
│  LLMClient（调用层）                                   │
│  ├── chat()              统一调用接口                  │
│  ├── 缓存               避免重复调用                   │
│  └── 调用日志            追踪每次调用                   │
│                                                        │
│  TemplateRegistry（模板管理）                           │
│  ├── register()          注册模板                      │
│  ├── get()               按名称/版本获取               │
│  └── list_all()          列出所有模板                   │
│                                                        │
│  PromptTemplate（模板）                                │
│  ├── fill()              变量填充                      │
│  ├── to_messages()       构建消息                      │
│  └── execute()           执行模板                      │
│                                                        │
│  BatchExecutor（批量执行）                              │
│  └── execute_batch()     批量处理                      │
│                                                        │
│  ABTester（A/B 测试）                                  │
│  └── test()              对比两个模板                   │
│                                                        │
│  Pipeline（管道编排）                                   │
│  ├── add_step()          添加步骤                      │
│  └── run()               执行管道                      │
│                                                        │
│  整合的知识点                                          │
│  ├── 第1课: Prompt结构/原则/参数                      │
│  ├── 第2课: Few-shot/CoT/ToT/ReAct                   │
│  ├── 第3课: 结构化输出/JSON/解析                      │
│  ├── 第4课: 角色设计/System Prompt/安全               │
│  ├── 第5课: 设计模式（分解/验证/管道）                │
│  └── 第6课: 优化/评估/版本管理/成本                   │
│                                                        │
│  统计:                                                 │
│    总调用: {stats['total_calls']}次                    │
│    缓存命中: {stats.get('cached_calls', 0)}次         │
│    平均延迟: {stats.get('avg_latency', 0):.0f}ms      │
│    模板数: {len(registry.templates)}                   │
│                                                        │
│  扩展方向                                              │
│  → Web UI（FastAPI + React 管理界面）                  │
│  → 接入多个 LLM 后端（OpenAI/Claude/本地）            │
│  → Prompt 自动优化（DSPy/OPRO）                       │
│  → 评估数据集管理                                     │
│  → 监控告警（准确率下降时通知）                       │
│  → 团队协作（权限/审批/发布流程）                     │
└────────────────────────────────────────────────────────┘
""")

print("=" * 60)
print("[完成] 第7课完成！你已经学会了：")
print("  [v] LLM 调用层（缓存+日志+统计）")
print("  [v] Prompt 模板管理（注册/版本/标签）")
print("  [v] 批量执行引擎")
print("  [v] A/B 测试框架")
print("  [v] 多步管道编排")
print("  [v] 整合前6课全部核心知识")
print("=" * 60)
print("\nlearn-prompt-engineering 课程全部完成！🎉")
