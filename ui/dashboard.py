import time
from typing import Optional

from core.models import Order
from services.metrics import Metrics


class Dashboard:
    def __init__(self, metrics: Metrics, interval: int = 5):
        self._metrics = metrics
        self._interval = interval
        self._last_order: Optional[Order] = None

    def start(self) -> None:
        while True:
            self._render()
            time.sleep(self._interval)

    def update_last_order(self, order: Order) -> None:
        self._last_order = order

    def _render(self) -> None:
        summary = self._metrics.summary()
        total_trades = summary.get("total_trades", 0)

        print(f"\n--- Dashboard ---")
        print(f"Total Trades: {total_trades}")

        if self._last_order:
            print(f"Last Order: {self._last_order.side.upper()} {self._last_order.quantity} {self._last_order.symbol}")
        else:
            print("Last Order: None")

        print("-----------------")
