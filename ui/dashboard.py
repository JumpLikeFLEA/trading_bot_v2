from collections import deque
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from core.models import Order, SignalType
from services.metrics import Metrics


class Dashboard:
    def __init__(self, metrics: Metrics, interval: int = 5):
        self._metrics = metrics
        self._interval = interval
        self._start_time = datetime.now()
        self._cycle_count = 0
        self._orders: deque = deque(maxlen=10)
        self._signals: Dict[str, Tuple[SignalType, float]] = {}
        self._last_order: Optional[Order] = None

    def update_last_order(self, order: Order, price: float = 0.0) -> None:
        self._last_order = order
        self._orders.append({
            "symbol": order.symbol,
            "side": order.side,
            "quantity": order.quantity,
            "price": order.price if hasattr(order, "price") and order.price else price,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })

    def increment_cycle(self) -> None:
        self._cycle_count += 1

    def update_signal(self, symbol: str, signal: SignalType, price: float) -> None:
        self._signals[symbol] = (signal, price)

    def _get_uptime(self) -> str:
        uptime = datetime.now() - self._start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def _get_win_rate(self, summary: Dict[str, Any]) -> str:
        wins = summary.get("wins", 0)
        losses = summary.get("losses", 0)
        total = wins + losses
        if total == 0:
            return "N/A"
        return f"{(wins / total * 100):.1f}%"

    def _color_signal(self, signal: SignalType) -> str:
        colors = {
            SignalType.BUY: "\033[32m",
            SignalType.SELL: "\033[31m",
            SignalType.HOLD: "\033[37m"
        }
        reset = "\033[0m"
        return f"{colors.get(signal, '\033[37m')}{signal.value}{reset}"

    def get_summary(self) -> str:
        summary = self._metrics.summary()
        total_trades = summary.get("total_trades", 0)
        portfolio_value = summary.get("portfolio_value", "N/A")
        pnl = summary.get("pnl", "N/A")
        win_rate = self._get_win_rate(summary)
        uptime = self._get_uptime()

        lines = []

        # Header
        lines.append(f"Trading Bot    Uptime: {uptime}")
        lines.append("")

        # Stats
        lines.append(f"Cycles: {self._cycle_count}")
        lines.append(f"Trades: {total_trades}")
        lines.append(f"Win Rate: {win_rate}")
        lines.append(f"Portfolio: {portfolio_value}")
        lines.append(f"P&L: {pnl}")
        lines.append("")

        # Recent Orders
        lines.append("Recent Orders:")
        recent_orders = list(self._orders)[-5:]
        if recent_orders:
            for order in reversed(recent_orders):
                side = order["side"].upper()
                qty_str = f"{order['quantity']:.4f}" if isinstance(order['quantity'], float) else str(order['quantity'])
                price_str = f"${order['price']:.2f}" if order['price'] else "$0.00"
                lines.append(f"  {side} {qty_str} {order['symbol']} @ {price_str} [{order['timestamp']}]")
        else:
            lines.append("  No orders yet")
        lines.append("")

        # Active Signals
        lines.append("Active Signals:")
        if self._signals:
            for symbol, (signal, price) in self._signals.items():
                colored_signal = self._color_signal(signal)
                reset = "\033[0m"
                lines.append(f"  {symbol}: {colored_signal}{reset}")
        else:
            lines.append("  No signals yet")

        return "\n".join(lines)

    def _render(self) -> None:
        print(self.get_summary())
