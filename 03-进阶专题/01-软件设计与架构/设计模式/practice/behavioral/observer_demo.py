"""观察者模式示例"""
from abc import ABC, abstractmethod


class Observer(ABC):
    @abstractmethod
    def update(self, event: str, data: dict): ...


class EventEmitter:
    def __init__(self):
        self._observers: list[Observer] = []

    def on(self, observer: Observer):
        self._observers.append(observer)

    def emit(self, event: str, data: dict):
        for observer in self._observers:
            observer.update(event, data)


class Logger(Observer):
    def update(self, event: str, data: dict):
        print(f"[LOG] {event}: {data}")


class Metrics(Observer):
    def update(self, event: str, data: dict):
        print(f"[METRICS] increment counter: {event}")


def main():
    emitter = EventEmitter()
    emitter.on(Logger())
    emitter.on(Metrics())

    emitter.emit("user_login", {"user_id": 42, "ip": "192.168.1.1"})
    emitter.emit("page_view", {"page": "/dashboard", "user_id": 42})


if __name__ == "__main__":
    main()
