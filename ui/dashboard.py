from typing import Optional

from core.models import Order
from services.metrics import Metrics


class Dashboard:
    def __init__(self, metrics: Metrics, interval: int = 5):
        self._metrics = metrics
        self._interval = interval
        self._last_order: Optional[Order] = None

    def update_last_order(self, order: Order) -> None:
        self._last_order = order

    def get_summary(self) -> str:
        summary = self._metrics.summary()
        total_trades = summary.get("total_trades", 0)

        if self._last_order:
            last_order_str = f"{self._last_order.side.upper()} {self._last_order.quantity} {self._last_order.symbol}"
        else:
            last_order_str = "None"

        return f"Total Trades: {total_trades}\nLast Order: {last_order_str}"

    def _render(self) -> None:
        print(f"\n--- Dashboard ---")
        print(self.get_summary())
        print("-----------------")
