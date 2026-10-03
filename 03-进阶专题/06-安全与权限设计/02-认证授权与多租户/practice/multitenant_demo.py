"""多租户最小可运行示例：共享表 + tenant_id + IDOR 防护。

对应第6课。运行方式：python multitenant_demo.py
"""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass


# 租户上下文：请求中间件写入，服务层读取，响应前清理
current_tenant: ContextVar[int | None] = ContextVar("current_tenant", default=None)


class TenantContext:
    @staticmethod
    def get() -> int:
        tenant_id = current_tenant.get()
        if tenant_id is None:
            raise RuntimeError("缺少租户上下文：请求未经过租户中间件")
        return tenant_id

    @staticmethod
    def set(tenant_id: int):
        return current_tenant.set(tenant_id)

    @staticmethod
    def reset(token) -> None:
        current_tenant.reset(token)


class NotFound(Exception):
    """资源不存在或不属于当前租户（统一返回 404）。"""


@dataclass
class Task:
    id: int
    tenant_id: int
    owner_id: int
    title: str


# 共享表：所有租户的数据在同一张"表"里
TASKS = [
    Task(1, 1, 100, "租户1 的任务A"),
    Task(2, 1, 100, "租户1 的任务B"),
    Task(101, 2, 200, "租户2 的任务A"),
    Task(102, 2, 201, "租户2 的任务B"),
]


def query_tasks() -> list[Task]:
    """列表查询：强制租户过滤，防串租户。"""
    tenant_id = TenantContext.get()
    return [t for t in TASKS if t.tenant_id == tenant_id]


def get_task(task_id: int) -> Task:
    """详情查询：对象级校验，越权返回 404（不泄露存在性）。"""
    tenant_id = TenantContext.get()
    for task in TASKS:
        if task.id == task_id:
            if task.tenant_id != tenant_id:
                raise NotFound("资源不存在")
            return task
    raise NotFound("资源不存在")


def tenant_report() -> dict:
    """报表/统计：同样强制租户过滤（最容易漏的位置之一）。"""
    tasks = query_tasks()
    return {"tenant_id": TenantContext.get(), "task_count": len(tasks)}


def main() -> None:
    # 模拟租户1 的请求
    token1 = TenantContext.set(1)
    try:
        assert [t.id for t in query_tasks()] == [1, 2]
        assert get_task(1).title == "租户1 的任务A"
        try:
            get_task(101)  # 租户2 的任务
            raise AssertionError("越权访问未被拦截！")
        except NotFound:
            pass
        print("租户1 任务:", [t.id for t in query_tasks()])
        print("租户1 报表:", tenant_report())
    finally:
        TenantContext.reset(token1)

    # 模拟租户2 的请求
    token2 = TenantContext.set(2)
    try:
        assert [t.id for t in query_tasks()] == [101, 102]
        try:
            get_task(1)  # 租户1 的任务
            raise AssertionError("越权访问未被拦截！")
        except NotFound:
            pass
        print("租户2 任务:", [t.id for t in query_tasks()])
        print("租户2 报表:", tenant_report())
    finally:
        TenantContext.reset(token2)

    # 缺少上下文时必须报错（防止"裸查询"）
    try:
        query_tasks()
        raise AssertionError("缺少租户上下文的查询未被拦截！")
    except RuntimeError:
        pass

    print("全部断言通过 OK")


if __name__ == "__main__":
    main()
