from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, List

from .models import Position, Signal, SignalType


class Strategy(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def on_data(self, data: Any) -> List[Signal]:
        pass

    def is_active(self, now: datetime) -> bool:
        """Check if strategy is active at given time. Defaults to always active."""
        return True

    def on_deactivate(self, positions: List[Position]) -> List[Signal]:
        """Generate SELL signals for all open positions when strategy deactivates."""
        signals = []
        for position in positions:
            if position.quantity > 0:
                signals.append(Signal(symbol=position.symbol, type=SignalType.SELL, strength=1.0))
        return signals
