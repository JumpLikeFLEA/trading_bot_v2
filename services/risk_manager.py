import logging
from abc import ABC, abstractmethod
from datetime import date
from typing import Dict, List, Optional, Tuple

from core.models import Order, Signal, SignalType
from services.portfolio import Portfolio


class RiskRule(ABC):
    @abstractmethod
    def check(self, signal: Signal, balance: float, price: float, portfolio: Portfolio) -> bool:
        ...

    def on_order_placed(self, order: Order) -> None:
        pass


class NoDoublePositionRule(RiskRule):
    def check(self, signal: Signal, balance: float, price: float, portfolio: Portfolio) -> bool:
        position = portfolio.get_position(signal.symbol)
        if signal.type == SignalType.SELL:
            if position is None or position.quantity <= 0:
                logging.warning(f"Cannot SELL {signal.symbol}: not owned")
                return False
        if position is not None:
            if signal.type == SignalType.BUY and position.quantity > 0:
                return False
            if signal.type == SignalType.SELL and position.quantity < 0:
                return False
        return True


class MaxSymbolExposureRule(RiskRule):
    def __init__(self, max_pct: float):
        self._max_pct = max_pct

    def check(self, signal: Signal, balance: float, price: float, portfolio: Portfolio) -> bool:
        if signal.type != SignalType.BUY:
            return True
        position = portfolio.get_position(signal.symbol)
        if position is None:
            return True
        exposure = position.quantity * position.entry_price
        if exposure >= balance * self._max_pct:
            logging.warning(
                f"Symbol exposure cap hit for {signal.symbol}: "
                f"${exposure:.2f} >= {self._max_pct:.0%} of balance"
            )
            return False
        return True


class MaxSectorExposureRule(RiskRule):
    def __init__(self, max_pct: float, sector_map: Dict[str, str]):
        self._max_pct = max_pct
        self._sector_map = sector_map

    def check(self, signal: Signal, balance: float, price: float, portfolio: Portfolio) -> bool:
        if signal.type != SignalType.BUY:
            return True
        sector = self._sector_map.get(signal.symbol, "Unknown")
        if sector == "Unknown":
            return True
        sector_exposure = sum(
            p.quantity * p.entry_price
            for p in portfolio.get_all_positions()
            if self._sector_map.get(p.symbol) == sector
        )
        if sector_exposure >= balance * self._max_pct:
            logging.warning(
                f"Sector exposure cap hit for '{sector}': "
                f"${sector_exposure:.2f} >= {self._max_pct:.0%} of balance"
            )
            return False
        return True


class MaxDailyLossRule(RiskRule):
    def __init__(self, max_loss_pct: float):
        self._max_loss_pct = max_loss_pct
        self._daily_pnl: float = 0.0
        self._last_reset: date = date.today()
        self._open_buys: Dict[str, Tuple[float, float]] = {}  # symbol → (price, qty)

    def _reset_if_new_day(self) -> None:
        today = date.today()
        if today != self._last_reset:
            self._daily_pnl = 0.0
            self._open_buys.clear()
            self._last_reset = today

    def check(self, signal: Signal, balance: float, price: float, portfolio: Portfolio) -> bool:
        self._reset_if_new_day()
        if self._daily_pnl <= -(balance * self._max_loss_pct):
            logging.warning(
                f"Daily loss limit reached: ${self._daily_pnl:.2f} loss "
                f"(limit {self._max_loss_pct:.0%} of balance)"
            )
            return False
        return True

    def on_order_placed(self, order: Order) -> None:
        self._reset_if_new_day()
        if order.side == "buy":
            self._open_buys[order.symbol] = (order.price, order.quantity)
        elif order.side == "sell" and order.symbol in self._open_buys:
            buy_price, buy_qty = self._open_buys.pop(order.symbol)
            self._daily_pnl += (order.price - buy_price) * min(order.quantity, buy_qty)


class RiskManager:
    def __init__(
        self,
        portfolio: Portfolio,
        rules: List[RiskRule],
        position_size_pct: float = 0.01,
    ):
        self._portfolio = portfolio
        self._rules = rules
        self._position_size_pct = position_size_pct

    def evaluate(self, signal: Signal, balance: float, price: float) -> Optional[Order]:
        if signal.type == SignalType.HOLD:
            return None

        for rule in self._rules:
            if not rule.check(signal, balance, price, self._portfolio):
                return None

        if signal.type == SignalType.SELL:
            position = self._portfolio.get_position(signal.symbol)
            quantity = position.quantity  # sell exactly what is held
        else:
            quantity = (balance * self._position_size_pct) / price
        side = "buy" if signal.type == SignalType.BUY else "sell"
        order = Order(symbol=signal.symbol, side=side, quantity=quantity, price=price)

        for rule in self._rules:
            rule.on_order_placed(order)

        return order
