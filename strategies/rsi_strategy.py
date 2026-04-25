from typing import Any

from core.models import Signal, SignalType
from core.strategy import Strategy


class RSIStrategy(Strategy):
    @property
    def name(self) -> str:
        return "RSIStrategy"

    def on_data(self, data: Any) -> Signal:
        rsi = data.get("rsi", 50.0)

        if rsi < 30:
            return Signal(symbol="AAPL", type=SignalType.BUY)
        elif rsi > 70:
            return Signal(symbol="AAPL", type=SignalType.SELL)
        else:
            return Signal(symbol="AAPL", type=SignalType.HOLD)
