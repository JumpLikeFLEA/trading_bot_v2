import logging
from typing import Dict, List

import yfinance as yf


class DataFeed:
    def __init__(
        self,
        symbols: List[str] = None,
        period: str = "5d",
        interval: str = "1h"
    ):
        if symbols is None:
            symbols = ["AAPL", "MSFT", "GOOGL", "AMZN"]
        self._symbols = symbols
        self._period = period
        self._interval = interval

        self._subindustry_cache: Dict[str, str] = {}
        for symbol in symbols:
            try:
                info = yf.Ticker(symbol).info
                self._subindustry_cache[symbol] = info.get("industry", "Unknown")
            except Exception as e:
                logging.warning(f"Could not fetch subindustry for {symbol}: {e}")
                self._subindustry_cache[symbol] = "Unknown"

    def get_data(self) -> Dict[str, Dict]:
        result = {}
        for symbol in self._symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=self._period, interval=self._interval)

                closes = hist["Close"].tolist()
                if len(closes) == 0:
                    logging.warning(f"No data for {symbol}, skipping")
                    continue

                price = closes[-1]

                opens = hist["Open"].tolist()

                result[symbol] = {
                    "price": price,
                    "closes": closes,
                    "opens": opens,
                    "subindustry": self._subindustry_cache.get(symbol, "Unknown")
                }
            except Exception as e:
                logging.warning(f"Error fetching data for {symbol}: {e}")
                continue

        return result
