"""只用训练集选择阈值，再在独立测试集上检查。数据是教学合成样例。"""
import argparse
import csv
import json
from pathlib import Path


def load_samples(path):
    rows = []
    with Path(path).open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != ["练习分钟", "通过", "划分"]:
            raise ValueError("列名应为：练习分钟、通过、划分")
        for number, row in enumerate(reader, 2):
            try:
                minutes, label = int(row["练习分钟"]), int(row["通过"])
            except (TypeError, ValueError) as error:
                raise ValueError(f"第{number}行数值错误") from error
            if minutes < 0 or label not in (0, 1) or row["划分"] not in {"train", "test"}:
                raise ValueError(f"第{number}行数据无效")
            rows.append({"minutes": minutes, "label": label, "split": row["划分"]})
    return rows


def fit_threshold(train):
    if not train or {row["label"] for row in train} != {0, 1}:
        raise ValueError("训练集必须包含两个类别")
    if any(row["split"] != "train" for row in train):
        raise ValueError("拟合时不得使用测试集")
    values = sorted({row["minutes"] for row in train})
    candidates = [values[0] - 1] + [(a + b) / 2 for a, b in zip(values, values[1:])] + [values[-1] + 1]
    # 同分时选较小阈值，保证结果可重复。
    return min(candidates, key=lambda threshold: (
        sum((row["minutes"] >= threshold) != bool(row["label"]) for row in train), threshold))


def evaluate(rows, threshold):
    if not rows:
        raise ValueError("评估集不能为空")
    matrix = {"TP": 0, "FP": 0, "TN": 0, "FN": 0}
    for row in rows:
        predicted, actual = row["minutes"] >= threshold, bool(row["label"])
        key = "TP" if predicted and actual else "FP" if predicted else "FN" if actual else "TN"
        matrix[key] += 1
    return {"count": len(rows), "accuracy": (matrix["TP"] + matrix["TN"]) / len(rows),
            "confusion_matrix": matrix}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(Path(__file__).with_name("分类样本.csv")))
    args = parser.parse_args()
    try:
        rows = load_samples(args.input)
        train = [row for row in rows if row["split"] == "train"]
        test = [row for row in rows if row["split"] == "test"]
        threshold = fit_threshold(train)
        print(json.dumps({"threshold": threshold, "train": evaluate(train, threshold),
                          "test": evaluate(test, threshold), "note": "教学合成数据，不能推断真实学生表现"},
                         ensure_ascii=False, indent=2))
    except (OSError, ValueError) as error:
        parser.exit(1, f"实验失败：{error}\n")


if __name__ == "__main__":
    main()
