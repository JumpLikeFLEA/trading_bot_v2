import logging
from typing import Optional

from core.models import Order, Signal, SignalType
from services.portfolio import Portfolio


class RiskManager:
    def __init__(self, portfolio: Portfolio):
        self._portfolio = portfolio

    def evaluate(self, signal: Signal, balance: float, price: float) -> Optional[Order]:
        if signal.type == SignalType.HOLD:
            return None

        if signal.type == SignalType.SELL:
            position = self._portfolio.get_position(signal.symbol)
            if position is None or position.quantity <= 0:
                logging.warning(f"Cannot SELL {signal.symbol}: not owned")
                return None

        position_size = (balance * 0.01) / price

        existing_position = self._portfolio.get_position(signal.symbol)
        if existing_position is not None:
            if signal.type == SignalType.BUY and existing_position.quantity > 0:
                return None
            if signal.type == SignalType.SELL and existing_position.quantity < 0:
                return None

        if signal.type == SignalType.BUY:
            side = "buy"
        elif signal.type == SignalType.SELL:
            side = "sell"
        else:
            return None

        return Order(
            symbol=signal.symbol,
            side=side,
            quantity=position_size
        )
