"""在临时英文路径验证Flutter工程，兼容分析器的中文路径问题。"""
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "02-方向选修/04-Flutter移动应用开发/起步工程"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, help="可写的英文临时目录；默认使用系统临时目录")
    args = parser.parse_args()
    base = (args.work_root or Path(tempfile.gettempdir())).resolve()
    if not str(base).isascii():
        parser.error("临时路径须为英文字符，请用--work-root指定，例如C:/course-temp")
    flutter = shutil.which("flutter")
    if not flutter:
        parser.error("未找到flutter，请先安装SDK并将其bin目录加入PATH")
    base.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="taskflow_flutter_", dir=base) as directory:
        working = Path(directory).resolve()
        if not working.is_relative_to(base):
            raise ValueError("临时目录不在指定工作目录内")
        for relative in ["lib", "test", "web"]:
            shutil.copytree(SOURCE / relative, working / relative)
        shutil.copy2(SOURCE / "pubspec.yaml", working / "pubspec.yaml")
        for arguments in [["--version"], ["pub", "get"], ["analyze"], ["test"], ["build", "web"]]:
            print("运行：flutter " + " ".join(arguments), flush=True)
            result = subprocess.run([flutter] + arguments, cwd=working, check=False)
            if result.returncode:
                return result.returncode
    print("Flutter起步工程验证通过；临时副本已清理。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
