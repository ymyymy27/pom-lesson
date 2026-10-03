"""RBAC 最小可运行示例：用户-角色-权限 + 角色继承。

对应第2课。运行方式：python rbac_demo.py
"""

from __future__ import annotations


class Permission:
    """权限点，例如 task:delete。"""

    def __init__(self, code: str, description: str = ""):
        self.code = code
        self.description = description


class Role:
    """角色：持有权限集合，可继承父角色（RBAC1）。"""

    def __init__(self, code: str, name: str, permissions=None, parents=None):
        self.code = code
        self.name = name
        self.permissions = set(permissions or [])
        self.parents = list(parents or [])

    def effective_permissions(self, seen=None) -> set[str]:
        """展开自身及所有父角色的权限 code，处理循环继承。"""
        seen = seen or set()
        if self in seen:
            return set()
        seen.add(self)
        result = {p.code for p in self.permissions}
        for parent in self.parents:
            result |= parent.effective_permissions(seen)
        return result


class User:
    def __init__(self, name: str):
        self.name = name
        self.roles: list[Role] = []

    def add_role(self, role: Role) -> None:
        self.roles.append(role)

    def has_permission(self, code: str) -> bool:
        return any(code in role.effective_permissions() for role in self.roles)

    def effective_permissions(self) -> set[str]:
        result: set[str] = set()
        for role in self.roles:
            result |= role.effective_permissions()
        return result


def main() -> None:
    # 权限点（code 采用 resource:action 规范）
    p_task_read = Permission("task:read", "查看任务")
    p_task_create = Permission("task:create", "创建任务")
    p_task_update = Permission("task:update", "更新任务")
    p_task_delete = Permission("task:delete", "删除任务")
    p_member_invite = Permission("member:invite", "邀请成员")
    p_role_manage = Permission("role:manage", "管理角色")

    # 角色：Member → Admin → Owner（继承链）
    member = Role("member", "成员", {p_task_read, p_task_create})
    admin = Role("admin", "管理员", {p_task_update, p_task_delete}, parents=[member])
    owner = Role("owner", "所有者", {p_member_invite, p_role_manage}, parents=[admin])

    alice = User("alice")
    alice.add_role(member)
    bob = User("bob")
    bob.add_role(admin)
    carol = User("carol")
    carol.add_role(owner)

    # 验证
    assert alice.has_permission("task:read")
    assert not alice.has_permission("task:delete")

    assert bob.has_permission("task:delete")      # 自己的权限
    assert bob.has_permission("task:read")        # 从 member 继承
    assert not bob.has_permission("role:manage")  # 未授予

    assert carol.has_permission("role:manage")    # 自己的权限
    assert carol.has_permission("task:delete")    # 从 admin 继承
    assert carol.has_permission("task:create")    # 从 member 继承

    print("alice 有效权限:", sorted(alice.effective_permissions()))
    print("bob   有效权限:", sorted(bob.effective_permissions()))
    print("carol 有效权限:", sorted(carol.effective_permissions()))
    print("全部断言通过 OK")


if __name__ == "__main__":
    main()
