import logging
from typing import Any, Dict, List, Optional

from core.models import Signal, SignalType
from core.strategy import Strategy


class OpenCloseRankStrategy(Strategy):
    """
    Alpha strategy based on rank(open / close).

    Parameters
    ----------
    Universe       : TOP 3000 US companies (filtered by caller or passed via symbols)
    Neutralization : Sub-industry (long/short legs are balanced within each sub-industry)
    Decay          : 7-day exponential decay applied to the raw signal
    Truncation     : 0.05  – individual weight capped at 5 % of gross exposure
    Pasteurization : True  – outlier scores are winsorized before ranking
    """

    def __init__(
        self,
        symbols: Optional[List[str]] = None,
        decay: int = 7,
        truncation: float = 0.05,
        pasteurize: bool = True,
        winsor_limit: float = 0.025,
        buy_quantile: float = 0.70,
        sell_quantile: float = 0.30,
    ):
        self._symbols = symbols
        self.DECAY = decay
        self.TRUNCATION = truncation
        self.PASTEURIZE = pasteurize
        self.WINSOR_LIMIT = winsor_limit
        self.BUY_QUANTILE = buy_quantile
        self.SELL_QUANTILE = sell_quantile
        # Rolling history:  {symbol: {"opens": [...], "closes": [...], "subindustry": str}}
        self._history: Dict[str, Dict] = {}

    # ------------------------------------------------------------------ #
    #  Identity                                                            #
    # ------------------------------------------------------------------ #
    @property
    def name(self) -> str:
        return "OpenCloseRankStrategy"

    # ------------------------------------------------------------------ #
    #  Public entry point                                                  #
    # ------------------------------------------------------------------ #
    def on_data(self, data: Any) -> List[Signal]:
        """
        Expected `data` schema (dict keyed by symbol)
        {
            "AAPL": {
                "opens":        [float, ...],   # chronological, len >= 1
                "closes":       [float, ...],   # chronological, len >= 1
                "subindustry":  str,            # e.g. "Software"
            },
            ...
        }
        """
        self._update_history(data)

        raw_scores = self._compute_raw_scores()
        if not raw_scores:
            return []

        if self.PASTEURIZE:
            raw_scores = self._winsorize(raw_scores)

        decayed = self._apply_decay(raw_scores)
        ranked = self._rank_normalize(decayed)
        neutralized = self._neutralize_subindustry(ranked)
        truncated = self._truncate(neutralized)

        return self._build_signals(truncated)

    # ------------------------------------------------------------------ #
    #  History management                                                  #
    # ------------------------------------------------------------------ #
    def _update_history(self, data: Dict) -> None:
        window = self.DECAY * 3          # keep enough bars for decay

        for symbol, values in data.items():
            if self._symbols is not None and symbol not in self._symbols:
                continue

            opens = values.get("opens", [])
            closes = values.get("closes", [])
            subindustry = values.get("subindustry", "Unknown")

            if symbol not in self._history:
                self._history[symbol] = {"opens": [], "closes": [], "subindustry": subindustry}

            rec = self._history[symbol]
            rec["subindustry"] = subindustry
            rec["opens"].extend(opens if isinstance(opens, list) else [opens])
            rec["closes"].extend(closes if isinstance(closes, list) else [closes])

            # trim to rolling window
            rec["opens"] = rec["opens"][-window:]
            rec["closes"] = rec["closes"][-window:]

    # ------------------------------------------------------------------ #
    #  Signal computation                                                  #
    # ------------------------------------------------------------------ #
    def _compute_raw_scores(self) -> Dict[str, float]:
        """Compute open/close ratio per bar, then decay-weight into a scalar."""
        scores: Dict[str, float] = {}

        for symbol, rec in self._history.items():
            opens = rec["opens"]
            closes = rec["closes"]
            n = min(len(opens), len(closes))

            if n < 1:
                logging.warning(f"[{self.name}] No data for {symbol}, skipping.")
                continue

            # per-bar ratio: open / close
            ratios = []
            for i in range(n):
                c = closes[i]
                if c == 0:
                    continue
                ratios.append(opens[i] / c)

            if not ratios:
                continue

            # exponential decay weights (most recent bar gets weight 1)
            weights = [self._decay_weight(n - 1 - i) for i in range(len(ratios))]
            total_w = sum(weights)
            if total_w == 0:
                continue

            scores[symbol] = sum(r * w for r, w in zip(ratios, weights)) / total_w

        return scores

    def _decay_weight(self, lag: int) -> float:
        """w = exp(-lag / decay)  →  lag=0 is the most recent bar."""
        import math
        return math.exp(-lag / self.DECAY)

    # ------------------------------------------------------------------ #
    #  Pasteurization (winsorization)                                      #
    # ------------------------------------------------------------------ #
    def _winsorize(self, scores: Dict[str, float]) -> Dict[str, float]:
        if len(scores) < 4:
            return scores

        vals = sorted(scores.values())
        lo_idx = max(0, int(len(vals) * self.WINSOR_LIMIT))
        hi_idx = min(len(vals) - 1, int(len(vals) * (1 - self.WINSOR_LIMIT)))
        lo, hi = vals[lo_idx], vals[hi_idx]

        return {s: max(lo, min(hi, v)) for s, v in scores.items()}

    # ------------------------------------------------------------------ #
    #  Decay already applied per-bar above; this step re-normalises       #
    # ------------------------------------------------------------------ #
    def _apply_decay(self, scores: Dict[str, float]) -> Dict[str, float]:
        # Decay is already embedded in _compute_raw_scores via per-bar weights.
        # This pass is kept as an explicit no-op hook for future extensions.
        return scores

    # ------------------------------------------------------------------ #
    #  Cross-sectional rank → [0, 1]                                      #
    # ------------------------------------------------------------------ #
    def _rank_normalize(self, scores: Dict[str, float]) -> Dict[str, float]:
        if not scores:
            return {}
        symbols = sorted(scores, key=scores.__getitem__)
        n = len(symbols)
        return {sym: i / (n - 1) if n > 1 else 0.5
                for i, sym in enumerate(symbols)}

    # ------------------------------------------------------------------ #
    #  Sub-industry neutralization                                         #
    # ------------------------------------------------------------------ #
    def _neutralize_subindustry(self, ranked: Dict[str, float]) -> Dict[str, float]:
        """
        Demean ranks within each sub-industry so net exposure per group ≈ 0.
        """
        from collections import defaultdict

        groups: Dict[str, List[str]] = defaultdict(list)
        for sym in ranked:
            grp = self._history[sym]["subindustry"]
            groups[grp].append(sym)

        neutralized: Dict[str, float] = {}
        for grp, members in groups.items():
            mean = sum(ranked[s] for s in members) / len(members)
            for s in members:
                neutralized[s] = ranked[s] - mean

        return neutralized

    # ------------------------------------------------------------------ #
    #  Truncation                                                          #
    # ------------------------------------------------------------------ #
    def _truncate(self, scores: Dict[str, float]) -> Dict[str, float]:
        """Cap absolute weight at TRUNCATION fraction of gross exposure."""
        if not scores:
            return {}

        gross = sum(abs(v) for v in scores.values())
        if gross == 0:
            return scores

        cap = self.TRUNCATION * gross
        truncated = {s: max(-cap, min(cap, v)) for s, v in scores.items()}

        # Re-normalise so gross exposure is preserved
        new_gross = sum(abs(v) for v in truncated.values())
        if new_gross > 0:
            scale = gross / new_gross
            truncated = {s: v * scale for s, v in truncated.items()}

        return truncated

    # ------------------------------------------------------------------ #
    #  Signal generation                                                   #
    # ------------------------------------------------------------------ #
    def _build_signals(self, scores: Dict[str, float]) -> List[Signal]:
        if not scores:
            return []

        vals = list(scores.values())
        lo = sorted(vals)[int(len(vals) * self.SELL_QUANTILE)]
        hi = sorted(vals)[int(len(vals) * self.BUY_QUANTILE)]

        signals: List[Signal] = []
        for symbol, score in scores.items():
            if score >= hi:
                sig_type = SignalType.BUY
            elif score <= lo:
                sig_type = SignalType.SELL
            else:
                sig_type = SignalType.HOLD

            signals.append(Signal(symbol=symbol, type=sig_type))

        return signals