from collections import deque
from datetime import datetime, timedelta
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
        self._line_count = 0

    def update_last_order(self, order: Order) -> None:
        self._last_order = order
        self._orders.append({
            "symbol": order.symbol,
            "side": order.side,
            "quantity": order.quantity,
            "price": order.price if hasattr(order, "price") else 0.0,
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

    def _format_box_line(self, left: str, right: str, width: int = 78) -> str:
        middle = width - len(left) - len(right) - 2
        return f"│ {left}{' ' * middle}{right} │"

    def get_summary(self) -> str:
        summary = self._metrics.summary()
        total_trades = summary.get("total_trades", 0)
        portfolio_value = summary.get("portfolio_value", "N/A")
        pnl = summary.get("pnl", "N/A")
        win_rate = self._get_win_rate(summary)
        uptime = self._get_uptime()

        lines = []
        lines.append("┌──────────────────────────────────────────────────────────────────────────────┐")
        lines.append(self._format_box_line("🤖 Trading Bot", f"Uptime: {uptime}"))
        lines.append("├──────────────────────────────────────────────────────────────────────────────┤")
        lines.append(self._format_box_line(
            f"Cycles: {self._cycle_count} | Trades: {total_trades} | Win Rate: {win_rate}",
            f"Portfolio: {portfolio_value} | P&L: {pnl}"
        ))
        lines.append("├──────────────────────────────────────────────────────────────────────────────┤")
        lines.append(self._format_box_line("📦 Recent Orders", ""))
        lines.append("├──────────────────────────────────────────────────────────────────────────────┤")

        # Recent orders header
        lines.append(f"│ {'Side':<6} {'Qty':<10} {'Symbol':<8} {'Price':<10} {'Time':<10} {'':>30} │")

        # Last 5 orders
        recent_orders = list(self._orders)[-5:]
        if recent_orders:
            for order in reversed(recent_orders):
                side_color = "\033[32m" if order["side"].upper() == "BUY" else "\033[31m"
                reset = "\033[0m"
                side_str = f"{side_color}{order['side'].upper():<6}{reset}"
                qty_str = f"{order['quantity']:.4f}" if isinstance(order['quantity'], float) else str(order['quantity'])
                price_str = f"${order['price']:.2f}" if order['price'] else "$0.00"
                line = f"│ {side_str} {qty_str:<10} {order['symbol']:<8} {price_str:<10} {order['timestamp']:<10} {'':>22} │"
                lines.append(line)
        else:
            lines.append(self._format_box_line("No orders yet", ""))

        # Pad to 5 lines
        while len([l for l in lines if "│" in l and "Side" not in l and "Orders" not in l and "───" not in l]) < 6 + len(recent_orders):
            lines.append(self._format_box_line("", ""))

        lines.append("├──────────────────────────────────────────────────────────────────────────────┤")
        lines.append(self._format_box_line("📊 Active Signals", f"({len(self._signals)} symbols)"))
        lines.append("├──────────────────────────────────────────────────────────────────────────────┤")

        # Signals grid - 4 columns
        if self._signals:
            signal_items = list(self._signals.items())
            for i in range(0, len(signal_items), 4):
                row_items = signal_items[i:i+4]
                row_parts = []
                for symbol, (signal, price) in row_items:
                    colored = self._color_signal(signal)
                    reset = "\033[0m"
                    cell = f"{symbol}: {colored}{reset}"
                    row_parts.append(cell)
                row = " | ".join(row_parts)
                padding = 76 - len(row.replace("\033[32m", "").replace("\033[31m", "").replace("\033[37m", "").replace("\033[0m", ""))
                lines.append(f"│ {row}{' ' * padding} │")
        else:
            lines.append(self._format_box_line("No signals yet", ""))

        lines.append("└──────────────────────────────────────────────────────────────────────────────┘")

        return "\n".join(lines)

    def _render(self) -> None:
        # Clear previous render using ANSI escape codes
        if self._line_count > 0:
            for _ in range(self._line_count):
                print("\033[F\033[K", end="")

        summary = self.get_summary()
        print(summary)
        self._line_count = summary.count("\n") + 1
