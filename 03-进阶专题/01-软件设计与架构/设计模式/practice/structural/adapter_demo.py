"""适配器模式示例：统一支付接口"""

from abc import ABC, abstractmethod


class PaymentProcessor(ABC):
    @abstractmethod
    def charge(self, amount: float, currency: str) -> dict: ...


class StripeGateway:
    """第三方 Stripe SDK（接口不兼容）"""

    def create_payment_intent(self, cents: int, curr: str) -> dict:
        return {"payment_intent_id": "pi_123", "status": "succeeded", "amount_cents": cents}


class StripeAdapter(PaymentProcessor):
    def __init__(self, gateway: StripeGateway):
        self._gateway = gateway

    def charge(self, amount: float, currency: str) -> dict:
        cents = int(amount * 100)
        result = self._gateway.create_payment_intent(cents, currency.upper())
        return {
            "transaction_id": result["payment_intent_id"],
            "status": result["status"],
            "amount": amount,
        }


class MockPayPalSDK:
    def send_payment(self, value: str, code: str) -> str:
        return f"PAYPAL-{value}-{code}"


class PayPalAdapter(PaymentProcessor):
    def __init__(self, sdk: MockPayPalSDK):
        self._sdk = sdk

    def charge(self, amount: float, currency: str) -> dict:
        txn_id = self._sdk.send_payment(str(amount), currency)
        return {"transaction_id": txn_id, "status": "completed", "amount": amount}


def checkout(processor: PaymentProcessor, amount: float):
    result = processor.charge(amount, "usd")
    print(f"Charged ${result['amount']} via {result['transaction_id']}")


def main():
    checkout(StripeAdapter(StripeGateway()), 99.99)
    checkout(PayPalAdapter(MockPayPalSDK()), 49.00)


if __name__ == "__main__":
    main()
