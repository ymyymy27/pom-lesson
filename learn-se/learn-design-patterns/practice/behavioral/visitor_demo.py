"""访问者模式示例：表达式树的求值与打印

场景：结构稳定（只有 Num / Add / Mul 三种节点），但操作常变
（求值、打印、类型检查、优化……）。

访问者把"操作"从节点类里搬出去：加一个新操作 = 加一个新 Visitor，
节点类一行不改（OCP）。

机关是双分派：element.accept(visitor) 内部再调用 visitor.visit_X(self)——
行为同时由"节点类型"和"访问者类型"两个运行时类型决定。
"""

from abc import ABC, abstractmethod


# --- 元素：结构稳定，每个元素实现 accept ---

class Expr(ABC):
    @abstractmethod
    def accept(self, visitor: "Visitor") -> object: ...


class Num(Expr):
    def __init__(self, value: int):
        self.value = value

    def accept(self, visitor: "Visitor") -> object:
        return visitor.visit_num(self)          # ★ 告诉访问者"我是 Num"


class Add(Expr):
    def __init__(self, left: Expr, right: Expr):
        self.left, self.right = left, right

    def accept(self, visitor: "Visitor") -> object:
        return visitor.visit_add(self)


class Mul(Expr):
    def __init__(self, left: Expr, right: Expr):
        self.left, self.right = left, right

    def accept(self, visitor: "Visitor") -> object:
        return visitor.visit_mul(self)


# --- 访问者：一个 Visitor = 一个"操作全家桶" ---

class Visitor(ABC):
    @abstractmethod
    def visit_num(self, node: Num) -> object: ...

    @abstractmethod
    def visit_add(self, node: Add) -> object: ...

    @abstractmethod
    def visit_mul(self, node: Mul) -> object: ...


class Evaluator(Visitor):                       # 操作1：求值
    def visit_num(self, node: Num) -> int:
        return node.value

    def visit_add(self, node: Add) -> int:
        return node.left.accept(self) + node.right.accept(self)   # 递归

    def visit_mul(self, node: Mul) -> int:
        return node.left.accept(self) * node.right.accept(self)


class Printer(Visitor):                         # 操作2：打印
    def visit_num(self, node: Num) -> str:
        return str(node.value)

    def visit_add(self, node: Add) -> str:
        return f"({node.left.accept(self)} + {node.right.accept(self)})"

    def visit_mul(self, node: Mul) -> str:
        return f"({node.left.accept(self)} * {node.right.accept(self)})"


def main():
    # 表达式: (1 + 2) * (3 + 4)
    expr = Mul(Add(Num(1), Num(2)), Add(Num(3), Num(4)))

    print("打印:", expr.accept(Printer()))
    print("求值:", expr.accept(Evaluator()))


if __name__ == "__main__":
    main()
