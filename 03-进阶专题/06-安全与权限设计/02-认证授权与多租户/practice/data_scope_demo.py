"""数据权限最小可运行示例：部门树 + 数据范围展开。

对应第4课。运行方式：python data_scope_demo.py
"""

from __future__ import annotations

from enum import Enum


class ScopeKind(Enum):
    SELF = "self"                    # 仅本人
    DEPT = "dept"                    # 本部门
    DEPT_AND_CHILDREN = "dept_and_children"  # 本部门及下属
    ALL = "all"                      # 租户内全部


# 部门树（扁平存储 + path 列，path 即"祖先链"）
DEPARTMENTS = {
    1: {"name": "公司", "path": "/1"},
    2: {"name": "技术部", "path": "/1/2"},
    3: {"name": "后端组", "path": "/1/2/3"},
    4: {"name": "前端组", "path": "/1/2/4"},
    5: {"name": "市场部", "path": "/1/5"},
}


class User:
    def __init__(self, name: str, department_id: int):
        self.name = name
        self.department_id = department_id


def descendants(department_id: int) -> list[int]:
    """返回某部门及其所有子部门 ID（利用 path 前缀）。"""
    path = DEPARTMENTS[department_id]["path"]
    return [did for did, dept in DEPARTMENTS.items() if dept["path"].startswith(path)]


class DataScope:
    def __init__(self, kind: ScopeKind, tenant_id: int, department_ids=None, user_id=None):
        self.kind = kind
        self.tenant_id = tenant_id
        self.department_ids = department_ids or []
        self.user_id = user_id

    def sql_condition(self, alias: str = "t") -> str:
        """生成伪 SQL 条件，演示最终注入查询的样子。"""
        if self.kind == ScopeKind.SELF:
            return f"{alias}.owner_id = {self.user_id}"
        if self.kind == ScopeKind.DEPT:
            return f"{alias}.department_id IN ({', '.join(map(str, self.department_ids))})"
        if self.kind == ScopeKind.DEPT_AND_CHILDREN:
            ids = ", ".join(map(str, self.department_ids))
            return f"{alias}.department_id IN ({ids})"
        if self.kind == ScopeKind.ALL:
            return f"{alias}.tenant_id = {self.tenant_id}"
        raise ValueError(f"未知范围: {self.kind}")


def resolve_data_scope(user: User, kind: ScopeKind, tenant_id: int) -> DataScope:
    """权限服务统一解析数据范围，业务代码不自己拼。"""
    if kind == ScopeKind.SELF:
        return DataScope(kind, tenant_id, user_id=user.id if hasattr(user, "id") else 1)
    if kind == ScopeKind.DEPT:
        return DataScope(kind, tenant_id, department_ids=[user.department_id])
    if kind == ScopeKind.DEPT_AND_CHILDREN:
        return DataScope(kind, tenant_id, department_ids=descendants(user.department_id))
    if kind == ScopeKind.ALL:
        return DataScope(kind, tenant_id)
    raise ValueError(f"未知范围: {kind}")


def main() -> None:
    zhang = User("zhang", department_id=3)  # 后端组
    li = User("li", department_id=2)        # 技术部
    tenant_id = 10

    scope_self = resolve_data_scope(zhang, ScopeKind.SELF, tenant_id)
    scope_dept = resolve_data_scope(zhang, ScopeKind.DEPT, tenant_id)
    scope_dept_children = resolve_data_scope(zhang, ScopeKind.DEPT_AND_CHILDREN, tenant_id)
    scope_all = resolve_data_scope(zhang, ScopeKind.ALL, tenant_id)

    assert descendants(3) == [3]
    assert descendants(2) == [2, 3, 4]
    assert scope_dept_children.department_ids == [3]
    assert scope_all.kind == ScopeKind.ALL

    print("zhang（后端组）本部门及下属:", scope_dept_children.department_ids)
    print("li（技术部）本部门及下属:   ", descendants(2))
    print()
    print("self   ->", scope_self.sql_condition())
    print("dept   ->", scope_dept.sql_condition())
    print("children ->", scope_dept_children.sql_condition())
    print("all    ->", scope_all.sql_condition())
    print("全部断言通过 OK")


if __name__ == "__main__":
    main()
