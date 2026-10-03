"""检查课程身份、先修、学时和必修配套；只使用标准库。"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check():
    data = json.loads((ROOT / "课程目录.yml").read_text(encoding="utf-8"))
    errors = []
    courses = data["courses"]
    by_id = {course["id"]: course for course in courses}
    if len(by_id) != len(courses):
        errors.append("duplicate course ids")
    seen_paths = set()
    valid_states = {"可试学", "已验证", "参考资料", "待SDK验证", "规划", "草稿", "已归档"}
    for course in courses:
        path = (ROOT / course["path"]).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():
            errors.append(f"missing or external course path: {course['id']}")
        if course["path"] in seen_paths:
            errors.append(f"duplicate path: {course['id']}")
        seen_paths.add(course["path"])
        if course["status"] not in valid_states:
            errors.append(f"invalid state: {course['id']}")
        for prerequisite in course["prerequisites"]:
            if prerequisite not in by_id:
                errors.append(f"missing prerequisite: {course['id']} -> {prerequisite}")
        if course["level"] == "基础必修":
            for suffix in ["示例/示例.py", "练习/练习.py", "练习/练习说明.md",
                           "参考答案/解题思路.md", "参考答案/参考答案.py", "验收标准.md"]:
                if not (path.parent / suffix).is_file():
                    errors.append(f"incomplete lesson: {course['id']} / {suffix}")
            if not isinstance(course["hours"], (int, float)) or course["hours"] <= 0:
                errors.append(f"invalid hours: {course['id']}")
    visited, active = set(), set()

    def visit(identity):
        if identity in active:
            errors.append(f"prerequisite cycle: {identity}")
            return
        if identity in visited or identity not in by_id:
            return
        active.add(identity)
        for prior in by_id[identity]["prerequisites"]:
            visit(prior)
        active.remove(identity)
        visited.add(identity)

    for identity in by_id:
        visit(identity)
    basic = [c for c in courses if c["level"] == "基础必修"]
    if len(basic) != 32 or sum(c["hours"] for c in basic) != 96:
        errors.append("basic curriculum must contain 32 lessons / 96 hours")
    for prefix in "WADF":
        units = [c for c in courses if c["id"].startswith(prefix)]
        if len(units) != 6 or sum(c["hours"] for c in units) != 72:
            errors.append(f"elective {prefix}: expected 6 units / 72 hours")
    projects = data.get("projects", [])
    if len(projects) != 4 or {p["direction"] for p in projects} != set("WADF"):
        errors.append("expected one project per elective direction")
    for project in projects:
        path = (ROOT / project["path"]).resolve()
        if project["hours"] != 24 or not path.is_relative_to(ROOT) or not path.is_file():
            errors.append(f"invalid elective project: {project['direction']}")
    return errors, len(courses)


if __name__ == "__main__":
    problems, count = check()
    for problem in problems:
        print(problem)
    print(f"Catalog: {count} entries, {len(problems)} errors")
    raise SystemExit(bool(problems))
