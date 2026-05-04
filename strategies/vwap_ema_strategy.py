import logging
from datetime import datetime, time
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from core.models import Signal, SignalType
from core.strategy import Strategy


class VWAPEMAStrategy(Strategy):
    """
    Intraday VWAP + EMA crossover strategy.

    Signal logic:
      BUY  — fast EMA crosses above slow EMA AND price is above VWAP
      SELL — fast EMA crosses below slow EMA AND price is below VWAP

    Designed for intraday intervals (1m, 3m, 5m, 15m).
    Expects `data` dict per symbol with keys:
      - "closes"  : List[float]
      - "highs"   : List[float]
      - "lows"    : List[float]
      - "volumes" : List[float]
    """

    def __init__(
        self,
        symbols: Optional[List[str]] = None,
        fast_period: int = 9,
        slow_period: int = 21,
    ):
        self._symbols = symbols
        self._fast = fast_period
        self._slow = slow_period

    # ------------------------------------------------------------------
    # Strategy interface
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return "VWAPEMAStrategy"

    def on_data(self, data: Any) -> List[Signal]:
        signals = []

        for symbol, values in data.items():
            if self._symbols is not None and symbol not in self._symbols:
                continue

            signal = self._process_symbol(symbol, values)
            signals.append(signal)

        return signals

    # ------------------------------------------------------------------
    # Activation controls
    # ------------------------------------------------------------------

    def is_active(self, now) -> bool:
        """Check if strategy is active during NYSE trading hours (Mon-Fri 09:30-15:50 ET)."""
        et_tz = ZoneInfo("America/New_York")
        et_time = now.astimezone(et_tz)

        # Monday = 0, Friday = 4
        if et_time.weekday() > 4:
            return False

        market_open = time(9, 30)
        market_close = time(15, 50)  # 10 min buffer before 16:00 close

        return market_open <= et_time.time() < market_close

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _process_symbol(self, symbol: str, values: Dict) -> Signal:
        closes = values.get("closes")
        highs = values.get("highs")
        lows = values.get("lows")
        volumes = values.get("volumes")
        timestamps = values.get("timestamps", [])

        # Guard: need enough bars for the slow EMA + 1 previous bar
        min_bars = self._slow + 1
        if not all(
            v is not None and len(v) >= min_bars
            for v in [closes, highs, lows, volumes]
        ):
            logging.warning(f"[{self.name}] Insufficient data for {symbol}, emitting HOLD")
            return Signal(symbol=symbol, type=SignalType.HOLD)

        et_tz = ZoneInfo("America/New_York")
        today = datetime.now(et_tz).date()
        today_indices = [
            i for i, ts in enumerate(timestamps)
            if ts.astimezone(et_tz).date() == today
        ]
        if not today_indices:
            logging.warning(f"[{self.name}] No today's bars for {symbol}, emitting HOLD")
            return Signal(symbol=symbol, type=SignalType.HOLD)

        today_closes = [closes[i] for i in today_indices]
        today_highs = [highs[i] for i in today_indices]
        today_lows = [lows[i] for i in today_indices]
        today_volumes = [volumes[i] for i in today_indices]

        if len(today_closes) == 0:
            logging.warning(f"[{self.name}] No today's bars for {symbol}, emitting HOLD")
            return Signal(symbol=symbol, type=SignalType.HOLD)

        vwap = self._calculate_vwap(today_closes, today_highs, today_lows, today_volumes)
        if vwap is None:
            logging.warning(f"[{self.name}] VWAP calculation failed for {symbol}, emitting HOLD")
            return Signal(symbol=symbol, type=SignalType.HOLD)

        # Current bar EMAs
        ema_fast_curr = self._calculate_ema(closes, self._fast)
        ema_slow_curr = self._calculate_ema(closes, self._slow)

        # Previous bar EMAs (drop the last close)
        ema_fast_prev = self._calculate_ema(closes[:-1], self._fast)
        ema_slow_prev = self._calculate_ema(closes[:-1], self._slow)

        if any(v is None for v in [ema_fast_curr, ema_slow_curr, ema_fast_prev, ema_slow_prev]):
            return Signal(symbol=symbol, type=SignalType.HOLD)

        price = closes[-1]
        signal_type = SignalType.HOLD

        fast_crossed_up = ema_fast_prev <= ema_slow_prev and ema_fast_curr > ema_slow_curr
        fast_crossed_down = ema_fast_prev >= ema_slow_prev and ema_fast_curr < ema_slow_curr

        if fast_crossed_up and price > vwap:
            signal_type = SignalType.BUY
        elif fast_crossed_down and price < vwap:
            signal_type = SignalType.SELL

        logging.info(
            f"[{self.name}] {symbol} | "
            f"Price: {price:.2f} | VWAP: {vwap:.2f} | "
            f"EMA{self._fast}: {ema_fast_curr:.2f} | EMA{self._slow}: {ema_slow_curr:.2f} | "
            f"Signal: {signal_type.name}"
        )
        return Signal(symbol=symbol, type=signal_type)

    def _calculate_ema(self, prices: List[float], period: int) -> Optional[float]:
        """Exponential Moving Average using the standard smoothing factor 2/(period+1)."""
        if len(prices) < period:
            return None

        k = 2.0 / (period + 1)
        ema = sum(prices[:period]) / period          # seed with SMA of first window
        for price in prices[period:]:
            ema = price * k + ema * (1 - k)
        return ema

    def _calculate_vwap(
        self,
        closes: List[float],
        highs: List[float],
        lows: List[float],
        volumes: List[float],
    ) -> Optional[float]:
        """
        Volume-Weighted Average Price over all available bars.
        Typical price = (high + low + close) / 3
        """
        total_volume = sum(volumes)
        if total_volume == 0:
            return None

        cumulative_tp_vol = sum(
            ((h + l + c) / 3) * v
            for h, l, c, v in zip(highs, lows, closes, volumes)
        )
        return cumulative_tp_vol / total_volume
