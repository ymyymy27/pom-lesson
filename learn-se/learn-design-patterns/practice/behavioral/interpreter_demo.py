"""解释器模式示例：表达式求值

每个语法规则对应一个类，interpret() 递归解释自己。
与访问者的对比：解释器把"解释逻辑"放在节点内部；
访问者把"操作"搬到外部。结构相同（都是树），分配不同。
"""

from abc import ABC, abstractmethod


class Expr(ABC):
    @abstractmethod
    def interpret(self) -> int: ...


class Num(Expr):                                # 终结符：叶子
    def __init__(self, value: int):
        self.value = value

    def interpret(self) -> int:
        return self.value


class Add(Expr):                                # 非终结符：复合规则
    def __init__(self, left: Expr, right: Expr):
        self.left, self.right = left, right

    def interpret(self) -> int:
        return self.left.interpret() + self.right.interpret()   # 递归


class Mul(Expr):
    def __init__(self, left: Expr, right: Expr):
        self.left, self.right = left, right

    def interpret(self) -> int:
        return self.left.interpret() * self.right.interpret()


def main():
    # 表达式: (1 + 2) * (3 + 4)
    expr = Mul(Add(Num(1), Num(2)), Add(Num(3), Num(4)))

    print("求值:", expr.interpret())


if __name__ == "__main__":
    main()
