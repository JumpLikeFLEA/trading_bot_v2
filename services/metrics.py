from typing import Dict, List, Tuple

from core.models import Order


class Metrics:
    def __init__(self):
        self._trades: List[Order] = []
        self._wins: int = 0
        self._losses: int = 0
        self._realized_pnl: float = 0.0
        self._open_buys: Dict[str, Tuple[float, float]] = {}  # symbol → (buy_price, quantity)
        self._portfolio_value: float = 0.0
        self._unrealized_pnl: float = 0.0

    def record_trade(self, order: Order) -> None:
        self._trades.append(order)
        if order.side == "buy":
            self._open_buys[order.symbol] = (order.price, order.quantity)
        elif order.side == "sell" and order.symbol in self._open_buys:
            buy_price, buy_qty = self._open_buys.pop(order.symbol)
            trade_pnl = (order.price - buy_price) * min(order.quantity, buy_qty)
            self._realized_pnl += trade_pnl
            if trade_pnl > 0:
                self._wins += 1
            else:
                self._losses += 1

    def update_portfolio_snapshot(self, value: float, unrealized_pnl: float) -> None:
        self._portfolio_value = value
        self._unrealized_pnl = unrealized_pnl

    def summary(self) -> Dict:
        return {
            "total_trades": len(self._trades),
            "wins": self._wins,
            "losses": self._losses,
            "realized_pnl": self._realized_pnl,
            "unrealized_pnl": self._unrealized_pnl,
            "pnl": self._realized_pnl + self._unrealized_pnl,
            "portfolio_value": self._portfolio_value,
        }
