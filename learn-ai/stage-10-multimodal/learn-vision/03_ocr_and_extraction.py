import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第3课：OCR 与信息提取
==============================================================================

OCR（Optical Character Recognition）= 光学字符识别
从图像中提取文字信息。

三种方案：
1. 多模态 LLM（GPT-4o/LLaVA）：灵活，理解上下文
2. 专用 OCR 引擎（PaddleOCR/EasyOCR）：快速，高精度
3. 云服务 OCR（百度/阿里/腾讯）：稳定，有免费额度

本课内容：
1. LLM 方式做 OCR
2. PaddleOCR 专用引擎
3. 表格识别与提取
4. 票据/证件信息提取
5. 手写体识别
6. OCR 后处理与结构化
==============================================================================
"""

import json
import base64
from io import BytesIO

print("=" * 60)
print("第3课：OCR 与信息提取")
print("=" * 60)

# ============================================================================
# 1. LLM 方式做 OCR
# ============================================================================
print("\n--- 1. LLM 方式做 OCR ---")
print("""
多模态 LLM 做 OCR 的优势：
✅ 不仅识别文字，还能理解含义
✅ 自动处理排版、方向、多语言
✅ 可以直接输出结构化结果
✅ 上下文理解（模糊文字可以推理）

劣势：
❌ 速度慢、成本高（按token计费）
❌ 对小文字、密集文字精度不够
❌ 不适合大批量处理

最佳 Prompt 模板：
""")

ocr_prompts = {
    "通用OCR": "请识别图片中的所有文字，按从上到下、从左到右的顺序输出。",
    "票据OCR": """识别这张票据/发票中的信息，以JSON格式输出：
{
  "type": "发票类型",
  "number": "发票号码",
  "date": "日期",
  "amount": "金额",
  "seller": "销售方",
  "buyer": "购买方",
  "items": [{"name": "项目", "quantity": "数量", "price": "单价"}]
}""",
    "名片OCR": """识别这张名片的信息，以JSON格式输出：
{
  "name": "姓名",
  "title": "职位",
  "company": "公司",
  "phone": "电话",
  "email": "邮箱",
  "address": "地址"
}""",
    "表格OCR": "识别图片中的表格，以Markdown表格格式输出。保持行列对齐。",
}

for name, prompt in ocr_prompts.items():
    print(f"\n  [{name}]")
    print(f"  Prompt: {prompt[:60]}...")

# 创建带文字的测试图像
try:
    from PIL import Image, ImageDraw

    def create_text_image(lines, size=(400, 200)):
        img = Image.new("RGB", size, color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        y = 20
        for line in lines:
            draw.text((20, y), line, fill=(0, 0, 0))
            y += 25
        return img

    def img_to_b64(img):
        buf = BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()

    # 模拟名片图像
    card_img = create_text_image([
        "张三 | 高级工程师",
        "AI科技有限公司",
        "Tel: 138-0000-1234",
        "Email: zhangsan@ai-tech.com",
        "北京市海淀区中关村大街1号",
    ], size=(350, 160))
    card_b64 = img_to_b64(card_img)
    print(f"\n  创建测试名片图像: {card_img.size}")
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    card_b64 = ""
    print("  Pillow 未安装，跳过图像生成")

# LLM OCR 调用
import httpx

def llm_ocr(image_b64: str, prompt: str, model: str = "llava:7b") -> str:
    try:
        resp = httpx.post("http://localhost:11434/api/chat", json={
            "model": model,
            "messages": [{"role": "user", "content": prompt, "images": [image_b64]}],
            "stream": False,
        }, timeout=60.0)
        return resp.json().get("message", {}).get("content", "无结果")
    except:
        return "Ollama 未连接或 llava 模型未安装"

if card_b64:
    print("\n[测试: LLM OCR 名片识别]")
    result = llm_ocr(card_b64, ocr_prompts["名片OCR"])
    print(f"  结果: {result[:200]}...")

# ============================================================================
# 2. PaddleOCR 专用引擎
# ============================================================================
print("\n--- 2. PaddleOCR 专用引擎 ---")
print("""
PaddleOCR 是百度开源的 OCR 工具，中文识别最强。

安装：pip install paddlepaddle paddleocr

```python
from paddleocr import PaddleOCR

ocr = PaddleOCR(use_angle_cls=True, lang='ch')

# 识别图片
result = ocr.ocr('invoice.jpg', cls=True)

for line in result[0]:
    bbox = line[0]        # 文字框坐标 [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
    text = line[1][0]     # 识别的文字
    confidence = line[1][1]  # 置信度 0-1
    print(f"{text} (置信度: {confidence:.2f})")
```

特点：
- 支持 80+ 语言
- 支持倾斜/弯曲文字
- 支持表格识别
- 支持版面分析
- 完全离线运行
""")

# ============================================================================
# 3. 表格识别与提取
# ============================================================================
print("\n--- 3. 表格识别与提取 ---")
print("""
表格 OCR 是最常见的需求之一。

方案对比：
┌──────────────────┬────────────┬────────────┬───────────┐
│  方案             │  简单表格  │  复杂表格  │  速度      │
├──────────────────┼────────────┼────────────┼───────────┤
│  GPT-4o          │  ★★★      │  ★★★      │  慢        │
│  PaddleOCR       │  ★★★      │  ★★       │  快        │
│  Camelot(PDF)    │  ★★★      │  ★★       │  快        │
│  Tabula(PDF)     │  ★★       │  ★        │  快        │
└──────────────────┴────────────┴────────────┴───────────┘

LLM 方式提取表格：
""")

if HAS_PIL:
    table_img = create_text_image([
        "姓名    部门    薪资",
        "张三    技术部  25000",
        "李四    产品部  22000",
        "王五    技术部  28000",
        "赵六    市场部  20000",
    ], size=(300, 170))
    table_b64 = img_to_b64(table_img)

    print("[测试: 表格 OCR]")
    result = llm_ocr(table_b64, "识别图中的表格，以Markdown表格格式输出。")
    print(f"  结果:\n  {result[:200]}...")

# ============================================================================
# 4. 票据/证件信息提取
# ============================================================================
print("\n--- 4. 票据信息提取 ---")
print("""
实际应用中最常见的 OCR 场景：

1. 增值税发票
   → 提取: 发票号、日期、金额、销售方、购买方
   
2. 银行回单
   → 提取: 交易流水号、金额、收付款方、日期

3. 身份证/护照
   → 提取: 姓名、证件号、出生日期、地址

4. 营业执照
   → 提取: 公司名、注册号、法人、经营范围

LLM OCR 的优势：不需要为每种票据单独训练模型！
只需要修改 Prompt 即可适配新的票据类型。
""")

# 模拟票据提取
print("[模拟: 发票信息提取]")
mock_invoice_result = {
    "type": "增值税普通发票",
    "number": "01234567",
    "date": "2024-03-15",
    "amount": "1,250.00",
    "tax": "162.50",
    "total": "1,412.50",
    "seller": "AI科技有限公司",
    "buyer": "数据智能公司",
    "items": [
        {"name": "技术服务费", "quantity": 1, "price": 1250.00}
    ]
}
print(f"  提取结果:")
print(f"  {json.dumps(mock_invoice_result, ensure_ascii=False, indent=2)}")

# ============================================================================
# 5. OCR 后处理与结构化
# ============================================================================
print("\n--- 5. OCR 后处理 ---")
print("""
原始 OCR 结果通常需要后处理：

1. 文本清洗
   - 去除多余空格和换行
   - 纠正常见错误（0→O, l→1）
   - 统一编码格式

2. 结构化提取
   - 正则表达式匹配（日期、金额、电话）
   - LLM 理解提取（更灵活）
   - 模板匹配（已知格式）

3. 置信度过滤
   - 低置信度文字标记或丢弃
   - 多次识别取共识

4. 排版还原
   - 按坐标重建行列
   - 表格结构还原
""")

import re

def post_process_ocr(raw_text: str) -> dict:
    """OCR 后处理示例"""
    result = {"raw": raw_text, "extracted": {}}

    # 提取日期
    dates = re.findall(r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?', raw_text)
    if dates:
        result["extracted"]["dates"] = dates

    # 提取金额
    amounts = re.findall(r'[¥￥]?\d{1,3}(?:,\d{3})*(?:\.\d{2})?元?', raw_text)
    if amounts:
        result["extracted"]["amounts"] = amounts

    # 提取电话
    phones = re.findall(r'1[3-9]\d{1}[-]?\d{4}[-]?\d{4}', raw_text)
    if phones:
        result["extracted"]["phones"] = phones

    # 提取邮箱
    emails = re.findall(r'[\w.-]+@[\w.-]+\.\w+', raw_text)
    if emails:
        result["extracted"]["emails"] = emails

    return result

# 测试后处理
test_text = "张三 138-0000-1234 zhangsan@ai.com 2024年3月15日 金额:¥1,250.00"
processed = post_process_ocr(test_text)
print(f"  原始文本: {test_text}")
print(f"  提取结果: {json.dumps(processed['extracted'], ensure_ascii=False)}")

# ============================================================================
# 6. 完整 OCR 流水线
# ============================================================================
print("\n--- 6. 完整 OCR 流水线 ---")
print("""
生产环境的 OCR 流水线：

  图像输入 → 预处理 → OCR引擎 → 后处理 → 结构化输出
                │                    │
          ┌─────┴─────┐      ┌──────┴──────┐
          │ 旋转矫正  │      │ 文本清洗    │
          │ 去噪增强  │      │ 正则提取    │
          │ 二值化    │      │ LLM结构化   │
          └───────────┘      └─────────────┘

混合方案（推荐）：
  PaddleOCR（快速提取文字）→ LLM（理解结构化）

```python
# 1. PaddleOCR 提取原始文字
ocr_result = paddleocr.ocr(image)
raw_text = "\\n".join([line[1][0] for line in ocr_result[0]])

# 2. LLM 结构化理解
prompt = f"以下是从发票OCR提取的文字，请结构化为JSON:\\n{raw_text}"
structured = llm.invoke(prompt)
```
""")

print("\n" + "=" * 60)
print("[完成] 第3课完成！你已经学会了：")
print("  [v] LLM 方式做 OCR（灵活+理解上下文）")
print("  [v] PaddleOCR 专用引擎（快速+高精度）")
print("  [v] 表格识别与提取")
print("  [v] 票据/证件信息提取")
print("  [v] OCR 后处理（正则+清洗+结构化）")
print("  [v] 混合 OCR 流水线（PaddleOCR + LLM）")
print("=" * 60)
print("\n下一课：04_object_detection.py - 目标检测与图像分割")
