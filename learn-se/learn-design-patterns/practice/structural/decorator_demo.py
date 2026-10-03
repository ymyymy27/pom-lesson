"""装饰器模式示例：HTTP 中间件链"""

from abc import ABC, abstractmethod
from typing import Callable


class Request:
    def __init__(self, path: str, headers: dict | None = None):
        self.path = path
        self.headers = headers or {}


class Response:
    def __init__(self, status: int, body: str):
        self.status = status
        self.body = body


Handler = Callable[[Request], Response]


class Application:
    def __init__(self):
        self.middlewares: list[Handler] = []
        self.routes: dict[str, Handler] = {}

    def use(self, middleware: Handler):
        self.middlewares.append(middleware)

    def route(self, path: str, handler: Handler):
        self.routes[path] = handler

    def handle(self, request: Request) -> Response:
        def dispatch(index: int) -> Response:
            if index < len(self.middlewares):
                return self.middlewares[index](request, lambda: dispatch(index + 1))
            handler = self.routes.get(request.path)
            if handler:
                return handler(request)
            return Response(404, "Not Found")

        return dispatch(0)


def logging_middleware(req: Request, next_handler: Callable) -> Response:
    print(f"[LOG] {req.path}")
    return next_handler()


def auth_middleware(req: Request, next_handler: Callable) -> Response:
    if "Authorization" not in req.headers:
        return Response(401, "Unauthorized")
    return next_handler()


def get_users(_req: Request) -> Response:
    return Response(200, '{"users": []}')


def main():
    app = Application()
    app.use(logging_middleware)
    app.use(auth_middleware)
    app.route("/api/users", get_users)

    r1 = app.handle(Request("/api/users"))
    print(f"No auth: {r1.status} {r1.body}")

    r2 = app.handle(Request("/api/users", {"Authorization": "Bearer token"}))
    print(f"With auth: {r2.status} {r2.body}")


if __name__ == "__main__":
    main()
