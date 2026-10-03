"""策略模式示例：购物车折扣"""

from abc import ABC, abstractmethod


class DiscountStrategy(ABC):
    @abstractmethod
    def calculate(self, total: float) -> float: ...


class NoDiscount(DiscountStrategy):
    def calculate(self, total: float) -> float:
        return total


class VIPDiscount(DiscountStrategy):
    def calculate(self, total: float) -> float:
        return total * 0.9


class WholesaleDiscount(DiscountStrategy):
    def calculate(self, total: float) -> float:
        return total * 0.7


class ShoppingCart:
    def __init__(self, strategy: DiscountStrategy | None = None):
        self.items: list[tuple[str, float]] = []
        self.strategy = strategy or NoDiscount()

    def add(self, name: str, price: float):
        self.items.append((name, price))

    def set_strategy(self, strategy: DiscountStrategy):
        self.strategy = strategy

    def total(self) -> float:
        subtotal = sum(price for _, price in self.items)
        return self.strategy.calculate(subtotal)


def main():
    cart = ShoppingCart()
    cart.add("Book", 50)
    cart.add("Pen", 10)

    print(f"Regular:   {cart.total():.2f}")

    cart.set_strategy(VIPDiscount())
    print(f"VIP:       {cart.total():.2f}")

    cart.set_strategy(WholesaleDiscount())
    print(f"Wholesale: {cart.total():.2f}")


if __name__ == "__main__":
    main()
