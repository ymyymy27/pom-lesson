"""检查仓库Markdown中的本地行内链接及引用式链接，不请求网络。"""
from pathlib import Path
import re
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {".git", "tmp", ".venv", "llm_env", "node_modules", "__pycache__", "build"}


def documents():
    return [p for p in ROOT.rglob("*.md") if not any(part in EXCLUDED for part in p.relative_to(ROOT).parts)]


def targets(text):
    text = re.sub(r"```.*?```|~~~.*?~~~", "", text, flags=re.S)
    values = re.findall(r"\]\((<[^>]+>|[^)]+)\)", text)
    values += re.findall(r"^\s*\[[^\]]+\]:\s*(\S+)", text, re.M)
    for raw in values:
        raw = raw.strip()
        if raw.startswith("<"):
            yield raw[1:raw.index(">")]
        else:
            yield re.split(r'\s+["\']', raw, maxsplit=1)[0]


def check():
    errors = []
    count = 0
    for source in documents():
        text = source.read_text(encoding="utf-8-sig")
        for target in targets(text):
            if target.startswith("#") or re.match(r"^[a-zA-Z][\w+.-]*:", target):
                continue
            path = unquote(target.split("#")[0])
            if not path:
                continue
            count += 1
            destination = (ROOT / path.lstrip("/")) if path.startswith("/") else source.parent / path
            if not destination.resolve().is_relative_to(ROOT) or not destination.exists():
                errors.append((source.relative_to(ROOT).as_posix(), target))
    return errors, count


if __name__ == "__main__":
    problems, count = check()
    for source, target in problems:
        print(f"{source} -> {target}")
    print(f"Links: {count} local targets, {len(problems)} errors")
    raise SystemExit(bool(problems))
