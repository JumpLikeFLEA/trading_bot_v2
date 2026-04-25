from typing import Optional

from core.models import Order, Signal, SignalType


class RiskManager:
    def evaluate(self, signal: Signal, balance: float) -> Optional[Order]:
        if signal.type == SignalType.HOLD:
            return None

        position_size = balance * 0.01

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
