import logging
from typing import Any, List, Optional

from core.models import Signal, SignalType
from core.strategy import Strategy


class MACrossoverStrategy(Strategy):
    def __init__(self, symbols: Optional[List[str]] = None):
        self._symbols = symbols
        self._fast: int = 10
        self._slow: int = 50

    @property
    def name(self) -> str:
        return "MACrossoverStrategy"

    def _calculate_ma(self, prices: List[float], period: int) -> Optional[float]:
        if len(prices) < period:
            return None
        return sum(prices[-period:]) / period

    def on_data(self, data: Any) -> List[Signal]:
        signals = []
        for symbol, values in data.items():
            if self._symbols is not None and symbol not in self._symbols:
                continue
            closes = values.get("closes")
            if closes is None or len(closes) < self._slow + 1:
                logging.warning(f"Insufficient data for {symbol}, emitting HOLD")
                signals.append(Signal(symbol=symbol, type=SignalType.HOLD))
                continue

            # Current bar MAs
            ma_fast_curr = self._calculate_ma(closes, self._fast)
            ma_slow_curr = self._calculate_ma(closes, self._slow)

            # Previous bar MAs (shift by one)
            ma_fast_prev = self._calculate_ma(closes[:-1], self._fast)
            ma_slow_prev = self._calculate_ma(closes[:-1], self._slow)

            signal_type = SignalType.HOLD

            if ma_fast_prev is not None and ma_slow_prev is not None:
                if ma_fast_prev <= ma_slow_prev and ma_fast_curr > ma_slow_curr:
                    signal_type = SignalType.BUY
                elif ma_fast_prev >= ma_slow_prev and ma_fast_curr < ma_slow_curr:
                    signal_type = SignalType.SELL

            logging.info(f"{symbol} MA{self._fast}: {ma_fast_curr:.2f}, MA{self._slow}: {ma_slow_curr:.2f}, Signal: {signal_type.name}")
            signals.append(Signal(symbol=symbol, type=signal_type))

        return signals
