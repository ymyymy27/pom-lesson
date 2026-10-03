import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第3课：会话管理与缓存
==============================================================================

AI 服务的两个核心工程问题：
  会话管理：多轮对话的上下文维护
  缓存：减少重复 LLM 调用，降低成本和延迟

本课内容：
1. 会话管理原理
2. 内存会话存储
3. 会话历史策略
4. 响应缓存
5. 语义缓存
6. 缓存策略对比
==============================================================================
"""

import json
import time
import hashlib
import uuid
from collections import OrderedDict

import httpx

OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen2.5:7b"

def chat(messages: list, temperature: float = 0.0) -> str:
    try:
        resp = httpx.post(f"{OLLAMA_URL}/api/chat", json={
            "model": MODEL, "messages": messages, "stream": False,
            "options": {"temperature": temperature, "num_predict": 300}
        }, timeout=30.0)
        return resp.json().get("message", {}).get("content", "")
    except:
        return f"[模拟回答] 基于 {len(messages)} 条消息的回复"

print("=" * 60)
print("第3课：会话管理与缓存")
print("=" * 60)

# ============================================================================
# 1. 会话管理原理
# ============================================================================
print("\n--- 1. 会话管理 ---")
print("""
LLM 本身无状态——每次调用都是独立的。
多轮对话需要手动维护历史消息。

  第1轮: messages = [system, user1]           → reply1
  第2轮: messages = [system, user1, reply1, user2] → reply2
  第3轮: messages = [system, user1, reply1, user2, reply2, user3] → reply3

问题：
  ❌ 消息越来越长 → token 成本增加
  ❌ 超过模型上下文窗口 → 报错
  ❌ 服务重启 → 历史丢失

解决：
  ✅ 会话存储（内存/Redis/数据库）
  ✅ 历史裁剪（保留最近N轮/摘要）
  ✅ 会话过期（TTL自动清理）
""")

# ============================================================================
# 2. 内存会话存储
# ============================================================================
print("\n--- 2. 会话存储 ---")

class SessionManager:
    """会话管理器"""

    def __init__(self, max_sessions: int = 1000, ttl: int = 3600):
        self.sessions = OrderedDict()  # 保持插入顺序，方便 LRU
        self.max_sessions = max_sessions
        self.ttl = ttl  # 秒

    def create_session(self, system_prompt: str = "") -> str:
        session_id = str(uuid.uuid4())[:8]
        self.sessions[session_id] = {
            "messages": [],
            "system_prompt": system_prompt,
            "created": time.time(),
            "last_active": time.time(),
            "turns": 0,
        }
        if system_prompt:
            self.sessions[session_id]["messages"].append(
                {"role": "system", "content": system_prompt}
            )
        self._cleanup()
        return session_id

    def add_message(self, session_id: str, role: str, content: str):
        if session_id not in self.sessions:
            raise ValueError(f"会话 {session_id} 不存在")
        self.sessions[session_id]["messages"].append(
            {"role": role, "content": content}
        )
        self.sessions[session_id]["last_active"] = time.time()
        if role == "user":
            self.sessions[session_id]["turns"] += 1

    def get_messages(self, session_id: str) -> list:
        if session_id not in self.sessions:
            raise ValueError(f"会话 {session_id} 不存在")
        return self.sessions[session_id]["messages"]

    def get_session_info(self, session_id: str) -> dict:
        s = self.sessions[session_id]
        return {
            "session_id": session_id,
            "turns": s["turns"],
            "messages": len(s["messages"]),
            "age_s": round(time.time() - s["created"]),
        }

    def delete_session(self, session_id: str):
        self.sessions.pop(session_id, None)

    def _cleanup(self):
        """清理过期和超量会话"""
        now = time.time()
        expired = [sid for sid, s in self.sessions.items()
                   if now - s["last_active"] > self.ttl]
        for sid in expired:
            del self.sessions[sid]
        while len(self.sessions) > self.max_sessions:
            self.sessions.popitem(last=False)  # LRU

    @property
    def active_count(self):
        return len(self.sessions)

session_mgr = SessionManager(ttl=3600)

# 创建会话
sid = session_mgr.create_session("你是一个友好的AI助手。请简洁回答。")
print(f"创建会话: {sid}")

# 多轮对话
turns = [
    "你好！我是小明。",
    "我正在学习 Python，有什么建议吗？",
    "你还记得我叫什么名字吗？",
]

for user_msg in turns:
    session_mgr.add_message(sid, "user", user_msg)
    messages = session_mgr.get_messages(sid)
    reply = chat(messages)
    session_mgr.add_message(sid, "assistant", reply)
    print(f"\n  User: {user_msg}")
    print(f"  AI:   {reply[:80]}...")

info = session_mgr.get_session_info(sid)
print(f"\n会话信息: {info}")

# ============================================================================
# 3. 历史裁剪
# ============================================================================
print("\n--- 3. 历史裁剪 ---")

class HistoryTrimmer:
    """历史消息裁剪器"""

    @staticmethod
    def trim_by_turns(messages: list, max_turns: int = 10) -> list:
        """保留最近 N 轮对话"""
        system = [m for m in messages if m["role"] == "system"]
        non_system = [m for m in messages if m["role"] != "system"]

        # 每轮 = user + assistant
        pairs = []
        for i in range(0, len(non_system), 2):
            pair = non_system[i:i+2]
            pairs.append(pair)

        kept_pairs = pairs[-max_turns:]
        result = system.copy()
        for pair in kept_pairs:
            result.extend(pair)
        return result

    @staticmethod
    def trim_by_tokens(messages: list, max_tokens: int = 4000) -> list:
        """按 token 数裁剪（简化：1字≈1.5token）"""
        system = [m for m in messages if m["role"] == "system"]
        non_system = [m for m in messages if m["role"] != "system"]

        result = system.copy()
        total = sum(len(m["content"]) * 1.5 for m in system)

        for msg in reversed(non_system):
            msg_tokens = len(msg["content"]) * 1.5
            if total + msg_tokens > max_tokens:
                break
            result.insert(len(system), msg)
            total += msg_tokens

        return result

    @staticmethod
    def summarize_history(messages: list, keep_recent: int = 4) -> list:
        """摘要旧历史 + 保留最近几轮"""
        system = [m for m in messages if m["role"] == "system"]
        non_system = [m for m in messages if m["role"] != "system"]

        if len(non_system) <= keep_recent * 2:
            return messages

        old = non_system[:-(keep_recent * 2)]
        recent = non_system[-(keep_recent * 2):]

        old_text = "\n".join(f"{m['role']}: {m['content'][:50]}" for m in old)
        summary = f"[历史摘要] 之前讨论了：{old_text[:200]}..."

        result = system.copy()
        result.append({"role": "system", "content": summary})
        result.extend(recent)
        return result

trimmer = HistoryTrimmer()

# 模拟长对话
long_messages = [{"role": "system", "content": "你是AI助手"}]
for i in range(20):
    long_messages.append({"role": "user", "content": f"问题{i+1}: 这是第{i+1}个问题"})
    long_messages.append({"role": "assistant", "content": f"回答{i+1}: 这是第{i+1}个回答"})

print(f"原始消息: {len(long_messages)} 条")
print(f"  按轮数裁剪(5轮): {len(trimmer.trim_by_turns(long_messages, 5))} 条")
print(f"  按token裁剪(2000): {len(trimmer.trim_by_tokens(long_messages, 2000))} 条")
print(f"  摘要+最近3轮: {len(trimmer.summarize_history(long_messages, 3))} 条")

# ============================================================================
# 4. 响应缓存
# ============================================================================
print("\n--- 4. 响应缓存 ---")

class ResponseCache:
    """LLM 响应缓存"""

    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.ttl = ttl
        self.stats = {"hits": 0, "misses": 0}

    def _key(self, messages: list, model: str) -> str:
        content = json.dumps(messages, sort_keys=True, ensure_ascii=False) + model
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, messages: list, model: str = MODEL) -> str:
        key = self._key(messages, model)
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry["time"] < self.ttl:
                self.stats["hits"] += 1
                self.cache.move_to_end(key)
                return entry["response"]
            else:
                del self.cache[key]
        self.stats["misses"] += 1
        return None

    def set(self, messages: list, model: str, response: str):
        key = self._key(messages, model)
        self.cache[key] = {"response": response, "time": time.time()}
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)

    @property
    def hit_rate(self):
        total = self.stats["hits"] + self.stats["misses"]
        return self.stats["hits"] / total if total > 0 else 0

cache = ResponseCache()

# 缓存演示
test_messages = [{"role": "user", "content": "什么是Python？"}]

# 第一次：未命中
result = cache.get(test_messages)
print(f"第1次查询: {'命中' if result else '未命中'}")
if not result:
    result = chat(test_messages)
    cache.set(test_messages, MODEL, result)
    print(f"  调用LLM并缓存: {result[:50]}...")

# 第二次：命中
result = cache.get(test_messages)
print(f"第2次查询: {'命中✓' if result else '未命中'}")
if result:
    print(f"  从缓存返回: {result[:50]}...")

print(f"命中率: {cache.hit_rate:.0%}")

# ============================================================================
# 5. 语义缓存
# ============================================================================
print("\n--- 5. 语义缓存 ---")
print("""
精确缓存：完全相同的输入才命中
  "什么是Python" ✓  →  命中
  "Python是什么" ✗  →  未命中（不同字符串）

语义缓存：语义相似的输入也能命中
  "什么是Python" ✓  →  命中
  "Python是什么" ✓  →  命中（语义相同！）
  "介绍一下Python" ✓  →  命中（语义相似！）

实现：
  1. 用 Embedding 计算查询向量
  2. 在缓存中找余弦相似度 > 阈值的条目
  3. 命中则返回缓存，未命中则调用 LLM

```python
class SemanticCache:
    def __init__(self, threshold=0.92):
        self.entries = []  # [(embedding, query, response)]
        self.threshold = threshold

    def get(self, query):
        q_emb = embed([query])[0]
        for emb, cached_query, response in self.entries:
            sim = cosine_sim(q_emb, emb)
            if sim >= self.threshold:
                return response  # 语义命中
        return None

    def set(self, query, response):
        q_emb = embed([query])[0]
        self.entries.append((q_emb, query, response))
```

注意：
  ✅ 大幅提高命中率
  ❌ 每次查询需要计算 Embedding
  ❌ 阈值需要调优（太低→错误命中，太高→命中率低）
  推荐阈值: 0.90-0.95
""")

# ============================================================================
# 6. 缓存策略
# ============================================================================
print("\n--- 6. 策略对比 ---")
print("""
┌──────────────────┬──────────┬──────────┬──────────────┐
│  策略             │  命中率   │  复杂度   │  适用场景     │
├──────────────────┼──────────┼──────────┼──────────────┤
│  精确缓存        │  低       │  简单    │  FAQ/固定问题 │
│  语义缓存        │  高       │  中      │  通用问答     │
│  多轮对话缓存    │  很低     │  简单    │  不推荐       │
│  分层缓存        │  高       │  高      │  生产环境     │
│  (精确+语义)     │          │          │              │
└──────────────────┴──────────┴──────────┴──────────────┘

生产缓存架构：
  L1: 精确缓存（内存/Redis，毫秒级）
  L2: 语义缓存（向量搜索，10-50ms）
  L3: LLM 调用（1-10秒）

  查询 → L1命中? → 返回
          ↓ 未命中
         L2命中? → 返回
          ↓ 未命中
         调用LLM → 存入L1+L2 → 返回

成本节省：
  假设每日 10000 次查询
  缓存命中率 40%
  节省 4000 次 LLM 调用
  OpenAI: 每次 $0.01 → 每日节省 $40
""")

print("=" * 60)
print("[完成] 第3课完成！你已经学会了：")
print("  [v] 会话管理（创建/存储/多轮对话）")
print("  [v] 历史裁剪（按轮数/token/摘要）")
print("  [v] 精确响应缓存（LRU+TTL）")
print("  [v] 语义缓存（Embedding相似度）")
print("  [v] 分层缓存架构")
print("  [v] 缓存成本节省计算")
print("=" * 60)
print("\n下一课：04_llm_router.py - LLM 路由")
