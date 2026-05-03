import logging
from typing import Dict, List

from core.strategy import Strategy
from strategies import MACrossoverStrategy, MATrendStrategy, RSIStrategy
from strategies.open_close_strategy import OpenCloseRankStrategy
from strategies.vwap_ema_strategy import VWAPEMAStrategy


def build_strategies(strategy_configs: List[Dict], strategy_filter: str = None) -> List[Strategy]:
    strategies = []
    for config in strategy_configs:
        name = config.get("name")
        symbols = config.get("symbols", [])

        # If strategy_filter is set, only build matching strategy regardless of active flag
        if strategy_filter is not None:
            if name != strategy_filter:
                continue
        else:
            # Otherwise respect the active flag (default True if absent)
            if not config.get("active", True):
                continue

        params = config.get("params", {})
        if name == "MACrossoverStrategy":
            strategies.append(MACrossoverStrategy(symbols=symbols, **params))
        elif name == "MATrendStrategy":
            strategies.append(MATrendStrategy(symbols=symbols, **params))
        elif name == "RSIStrategy":
            strategies.append(RSIStrategy(symbols=symbols, **params))
        elif name == "OpenCloseRankStrategy":
            strategies.append(OpenCloseRankStrategy(symbols=symbols, **params))
        elif name == "VWAPEMAStrategy":
            strategies.append(VWAPEMAStrategy(symbols=symbols, fast_period=params.get("fast_period", 9), slow_period=params.get("slow_period", 21)))
        else:
            logging.warning(f"Unrecognised strategy name: {name}, skipping")

    return strategies
