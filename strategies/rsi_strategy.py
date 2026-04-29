import logging
from typing import Any, Dict, List, Optional

from core.models import Signal, SignalType
from core.strategy import Strategy


class RSIStrategy(Strategy):
    def __init__(self, symbols: Optional[List[str]] = None):
        self._symbols = symbols

    @property
    def name(self) -> str:
        return "RSIStrategy"

    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        if len(prices) < period + 1:
            return 50.0

        gains = []
        losses = []

        for i in range(1, period + 1):
            change = prices[-period - 1 + i] - prices[-period - 2 + i]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def on_data(self, data: Any) -> List[Signal]:
        signals = []
        for symbol, values in data.items():
            if self._symbols is not None and symbol not in self._symbols:
                continue
            closes = values.get("closes")
            if closes is None or len(closes) < 15:
                logging.warning(f"Insufficient data for {symbol}, emitting HOLD")
                signals.append(Signal(symbol=symbol, type=SignalType.HOLD))
                continue

            rsi = self._calculate_rsi(closes)
            logging.info(f"{symbol} RSI: {rsi:.2f}")

            if rsi < 30:
                signals.append(Signal(symbol=symbol, type=SignalType.BUY))
            elif rsi > 70:
                signals.append(Signal(symbol=symbol, type=SignalType.SELL))
            else:
                signals.append(Signal(symbol=symbol, type=SignalType.HOLD))

        return signals
