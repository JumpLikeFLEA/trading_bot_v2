from typing import Dict, List

from core.models import Order


class Metrics:
    def __init__(self):
        self._trades: List[Order] = []

    def record_trade(self, order: Order) -> None:
        self._trades.append(order)

    def summary(self) -> Dict[str, int]:
        return {
            "total_trades": len(self._trades)
        }
