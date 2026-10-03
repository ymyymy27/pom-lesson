"""核对旧文件去向与保留资源的 SHA256，避免迁移丢失文件。"""
import csv
import hashlib
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def check():
    manifest = ROOT / "06-教学管理/文件迁移清单.csv"
    with manifest.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    errors = []
    original_paths, targets = set(), set()
    for row in rows:
        original = row["原路径"]
        target = (ROOT / row["新路径"]).resolve()
        if original in original_paths or target in targets:
            errors.append(f"duplicate migration: {original}")
        original_paths.add(original)
        targets.add(target)
        if not target.is_relative_to(ROOT) or not target.is_file():
            errors.append(f"missing or external target: {original}")
            continue
        if not re.fullmatch(r"[0-9a-f]{64}", row["原始SHA256"]):
            errors.append(f"invalid original digest: {original}")
        if row["验证结果"] == "待统一检查":
            errors.append(f"unverified migration: {original}")
        if row["验证结果"].startswith("原内容保留"):
            data = target.read_bytes()
            if row["校验方式"] == "UTF-8文本；CRLF规范化为LF":
                data = data.replace(b"\r\n", b"\n")
            elif row["校验方式"] != "原始字节":
                errors.append(f"invalid preservation check: {original}")
            expected = row["保留内容校验SHA256"]
            if not re.fullmatch(r"[0-9a-f]{64}", expected):
                errors.append(f"invalid preservation digest: {original}")
            digest = hashlib.sha256(data).hexdigest()
            if digest != expected:
                errors.append(f"preserved content changed: {original}")
    if len(rows) != 922:
        errors.append("migration must account for the original 922 files")
    return errors, len(rows)


if __name__ == "__main__":
    problems, count = check()
    for problem in problems:
        print(problem)
    print(f"Migration: {count} entries, {len(problems)} errors")
    raise SystemExit(bool(problems))
