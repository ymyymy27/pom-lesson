import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "04-项目实践/01-TaskFlow校园任务助手"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


memory = load("memory_tasks", TASK / "第一版-内存列表/任务助手.py")
json_tasks = load("json_tasks", TASK / "第二版-JSON文件保存/任务助手.py")
sql_tasks = load("sql_tasks", TASK / "第三版-SQLite与协作/任务助手.py")
rag = load("rag", ROOT / "04-项目实践/02-RAG课程资料问答助手/问答助手.py")
analysis = load("analysis", ROOT / "04-项目实践/03-校园数据分析/分析.py")
baseline = load("baseline", ROOT / "04-项目实践/03-校园数据分析/分类基线.py")


class TaskTests(unittest.TestCase):
    def test_memory_and_input_contract(self):
        tasks = []
        memory.add_task(tasks, " 阅读 ")
        self.assertEqual(tasks[0]["title"], "阅读")
        memory.complete_task(tasks, 1)
        self.assertTrue(tasks[0]["done"])
        with self.assertRaises(ValueError):
            memory.add_task(tasks, "  ")
        with self.assertRaises(ValueError):
            memory.complete_task(tasks, 9)

    def test_json_persistence_and_bad_file_preservation(self):
        with tempfile.TemporaryDirectory(prefix="JSON 中文路径 ") as directory:
            path = Path(directory) / "tasks.json"
            json_tasks.execute(path, "add", title="实验")
            json_tasks.execute(path, "done", task_id=1)
            self.assertTrue(json_tasks.execute(path, "list")[0]["done"])
            path.write_text("{bad", encoding="utf-8")
            with self.assertRaises(ValueError):
                json_tasks.execute(path, "add", title="不覆盖")
            self.assertEqual(path.read_text(encoding="utf-8"), "{bad")
            for invalid in [None, [{"id": True, "title": "x", "done": False}],
                            [{"id": 1, "title": "x", "done": "false"}]]:
                path.write_text(json.dumps(invalid), encoding="utf-8")
                with self.assertRaises(ValueError):
                    json_tasks.load(path)

    def test_sql_persistence_parameterization_and_missing_ids(self):
        with tempfile.TemporaryDirectory(prefix="SQLite 中文路径 ") as directory:
            path = Path(directory) / "tasks.sqlite3"
            title = "'; DROP TABLE tasks; --"
            first = sql_tasks.execute(path, "add", title=title)
            self.assertEqual(first[0]["title"], title)
            sql_tasks.execute(path, "done", task_id=first[0]["id"])
            self.assertTrue(sql_tasks.execute(path, "list")[0]["done"])
            with self.assertRaises(ValueError):
                sql_tasks.execute(path, "delete", task_id=999)
            self.assertEqual(len(sql_tasks.execute(path, "list")), 1)
            sql_tasks.execute(path, "delete", task_id=first[0]["id"])
            second = sql_tasks.execute(path, "add", title="第二条")
            self.assertGreater(second[0]["id"], first[0]["id"])

    def test_cli_across_processes(self):
        with tempfile.TemporaryDirectory(prefix="CLI 空格目录 ") as directory:
            path = str(Path(directory) / "tasks.sqlite3")
            script = str(TASK / "第三版-SQLite与协作/任务助手.py")
            for action in [["add", "--title", "reading"], ["done", "--id", "1"], ["list"]]:
                result = subprocess.run([sys.executable, script, "--db", path] + action,
                                        capture_output=True, check=True)
            self.assertIs(json.loads(result.stdout)[0]["done"], True)


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.documents = json.loads((ROOT / "04-项目实践/02-RAG课程资料问答助手/课程资料.json").read_text(encoding="utf-8"))

    def test_expected_sources_and_no_evidence(self):
        questions = json.loads((ROOT / "04-项目实践/02-RAG课程资料问答助手/评估问题.json").read_text(encoding="utf-8"))
        for method in ["keyword", "vector"]:
            for item in questions:
                with self.subTest(method=method, question=item["question"]):
                    result = rag.ask(item["question"], self.documents, method)
                    found = result["sources"][0]["source"] if result["sources"] else None
                    self.assertEqual(found, item["expected"])
                    if found:
                        source = next(d for d in self.documents if d["id"] == found)
                        self.assertEqual(result["answer"], source["text"])
                    else:
                        self.assertIn("没有", result["answer"])

    def test_empty_inputs_and_invalid_method(self):
        self.assertEqual(rag.retrieve("", self.documents), [])
        self.assertEqual(rag.retrieve("Git", []), [])
        with self.assertRaises(ValueError):
            rag.retrieve("Git", self.documents, "unknown")


class DataTests(unittest.TestCase):
    def test_statistics_and_bad_rows(self):
        groups = analysis.summarize(ROOT / "04-项目实践/03-校园数据分析/学习记录.csv")
        self.assertEqual(groups["Python"], {"count": 3, "minutes": 100, "done": 2})
        self.assertIn("66.7%", analysis.report(groups))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.csv"
            for data in ["课程,学习分钟,完成\nPython,-1,1\n", "课程,学习分钟,完成\nPython,x,1\n", "a,b,c\n1,2,3\n"]:
                path.write_text(data, encoding="utf-8")
                with self.assertRaises(ValueError):
                    analysis.summarize(path)
            path.write_text("课程,学习分钟,完成\n", encoding="utf-8")
            self.assertEqual(analysis.summarize(path), {})

    def test_train_only_fit_and_known_confusion_matrix(self):
        rows = baseline.load_samples(ROOT / "04-项目实践/03-校园数据分析/分类样本.csv")
        train = [r for r in rows if r["split"] == "train"]
        test = [r for r in rows if r["split"] == "test"]
        threshold = baseline.fit_threshold(train)
        self.assertEqual(threshold, 27.5)
        self.assertEqual(baseline.evaluate(train, threshold)["accuracy"], 1)
        self.assertEqual(baseline.evaluate(test, threshold)["confusion_matrix"], {"TP": 1, "FP": 1, "TN": 1, "FN": 1})
        with self.assertRaises(ValueError):
            baseline.fit_threshold(rows)
        with self.assertRaises(ValueError):
            baseline.evaluate([], threshold)


if __name__ == "__main__":
    unittest.main()
