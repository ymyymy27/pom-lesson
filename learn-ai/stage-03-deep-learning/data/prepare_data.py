import json
import os
import glob
import random
from pathlib import Path

DATA_DIR = Path("e:/temp-chinese-poetry")

def load_poetry():
    """加载所有唐诗和宋词"""
    poems = []

    # 加载唐诗
    tang_files = glob.glob(str(DATA_DIR / "strains/json/poet.tang.*.json"))
    for f in tang_files:
        try:
            with open(f, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
                if isinstance(data, list):
                    poems.extend(data)
                elif isinstance(data, dict):
                    poems.append(data)
        except Exception as e:
            print(f"读取唐诗失败 {f}: {e}")

    # 加载宋词
    ci_files = glob.glob(str(DATA_DIR / "*/ci.song.*.json"))
    for f in ci_files:
        try:
            with open(f, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
                if isinstance(data, list):
                    poems.extend(data)
                elif isinstance(data, dict):
                    poems.append(data)
        except Exception as e:
            print(f"读取宋词失败 {f}: {e}")

    return poems

def poems_to_text(poems, split="="*40):
    """将诗歌转换为纯文本"""
    lines = []

    for p in poems:
        # 提取诗歌内容
        if 'paragraphs' in p:
            content_lines = p['paragraphs']
        elif 'content' in p:
            content_lines = p['content']
        elif '句子' in p:
            content_lines = p['句子']
        else:
            continue

        # 清理并添加
        for line in content_lines:
            line = line.strip()
            if line:
                lines.append(line)

        # 添加分隔符（让模型学习换行）
        lines.append(split)

    return '\n'.join(lines)

def main():
    OUT_DIR = Path("e:/code/Projects/learn/learn-ai/stage-03-deep-learning/data")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("加载诗歌数据...")
    poems = load_poetry()
    print(f"共加载 {len(poems):,} 首诗歌")

    # 打乱顺序
    random.shuffle(poems)

    # 划分训练集和验证集
    val_size = int(len(poems) * 0.1)
    val_poems = poems[:val_size]
    train_poems = poems[val_size:]

    print(f"训练集: {len(train_poems):,} 首")
    print(f"验证集: {len(val_poems):,} 首")

    # 转换文本
    print("转换为文本...")
    train_text = poems_to_text(train_poems)
    val_text = poems_to_text(val_poems)

    # 保存
    train_path = OUT_DIR / "train.txt"
    val_path = OUT_DIR / "val.txt"

    with open(train_path, 'w', encoding='utf-8') as f:
        f.write(train_text)
    print(f"训练集已保存: {train_path} ({len(train_text):,} 字符)")

    with open(val_path, 'w', encoding='utf-8') as f:
        f.write(val_text)
    print(f"验证集已保存: {val_path} ({len(val_text):,} 字符)")

    # 统计字符集
    all_text = train_text + val_text
    chars = sorted(set(all_text))
    print(f"字符集大小: {len(chars)}")

    # 统计样例
    print("\n--- 训练集样例 (前500字符) ---")
    print(train_text[:500])

if __name__ == "__main__":
    main()
