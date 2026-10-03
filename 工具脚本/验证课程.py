"""运行基础示例、核对答案、检查Python语法和离线项目行为。"""
import argparse
import ast
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from 检查课程目录 import check as catalog_check
from 检查课程链接 import check as link_check
from 检查迁移清单 import check as migration_check


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--django-python", help="已安装项目依赖的Python路径")
    args = parser.parse_args()
    failures = []
    for name, check in [("catalog", catalog_check), ("links", link_check), ("migration", migration_check)]:
        errors, count = check()
        print(f"{name}: {count}, errors={len(errors)}")
        failures.extend(str(e) for e in errors)
    excluded = {".git", "tmp", ".venv", "llm_env", "__pycache__", "node_modules"}
    scripts = [p for p in ROOT.rglob("*.py") if not any(part in excluded for part in p.relative_to(ROOT).parts)]
    for path in scripts:
        try:
            ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        except (SyntaxError, UnicodeError) as error:
            failures.append(f"syntax: {path.relative_to(ROOT)}: {error}")
    print(f"syntax: {len(scripts)} files")
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    courses = json.loads((ROOT / "课程目录.yml").read_text(encoding="utf-8"))["courses"]
    count = 0
    with tempfile.TemporaryDirectory(prefix="课程 空格验证 ") as directory:
        for course in courses:
            if course["level"] != "基础必修":
                continue
            base = (ROOT / course["path"]).parent
            exercise = (base / "练习/练习说明.md").read_text(encoding="utf-8")
            expected = re.search(r"固定示例的参考输出：\s*```text\n(.*?)\n```", exercise, re.S).group(1)
            for relative in ["示例/示例.py", "参考答案/参考答案.py"]:
                result = subprocess.run([sys.executable, str(base / relative)], cwd=directory,
                                        capture_output=True, text=True, encoding="utf-8", env=env, timeout=15)
                count += 1
                if result.returncode:
                    failures.append(f"run: {course['id']} {relative}: {result.stderr}")
                elif relative.startswith("参考答案") and result.stdout.strip() != expected.strip():
                    failures.append(f"output: {course['id']}: expected={expected!r}, actual={result.stdout!r}")
    print(f"basic runs: {count}")
    suite = unittest.defaultTestLoader.discover(str(ROOT / "工具脚本/测试"), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        failures.append("offline project tests failed")
    if args.django_python:
        project = ROOT / "04-项目实践/01-TaskFlow校园任务助手/第四版-Django网页应用"
        for command in [["manage.py", "check"], ["manage.py", "makemigrations", "--check", "--dry-run"], ["manage.py", "test"]]:
            result = subprocess.run([args.django_python] + command, cwd=project, env=env,
                                    capture_output=True, text=True, encoding="utf-8", timeout=90)
            print("Django:", " ".join(command), "exit=", result.returncode)
            if result.returncode:
                failures.append(result.stdout + result.stderr)
    else:
        print("Django: not run; provide --django-python after installing project requirements")
    for failure in failures:
        print(failure)
    print(f"Validation failures: {len(failures)}")
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
