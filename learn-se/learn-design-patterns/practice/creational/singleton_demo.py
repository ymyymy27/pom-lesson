"""单例模式示例：应用配置（线程安全）"""

from threading import Lock


class AppConfig:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.debug = False
        self.database_url = "sqlite:///app.db"
        self._initialized = True

    def load_from_env(self, env: dict):
        self.debug = env.get("DEBUG", "false").lower() == "true"
        self.database_url = env.get("DATABASE_URL", self.database_url)


def main():
    a = AppConfig()
    b = AppConfig()
    print(f"同一实例: {a is b}")

    a.load_from_env({"DEBUG": "true", "DATABASE_URL": "postgresql://localhost/taskflow"})
    print(f"debug={b.debug}, db={b.database_url}")


if __name__ == "__main__":
    main()
