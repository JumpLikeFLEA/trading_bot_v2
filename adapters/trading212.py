from typing import List

from adapters.broker import Broker
from core.models import Order, Position


class Trading212Broker(Broker):
    def __init__(self, api_key: str, secret: str):
        self._api_key = api_key
        self._secret = secret

    def get_balance(self) -> float:
        return 10000.0

    def get_positions(self) -> List[Position]:
        return []

    def place_order(self, order: Order) -> None:
        print(f"[Trading212] Order placed: {order.side.upper()} {order.quantity} {order.symbol}")
