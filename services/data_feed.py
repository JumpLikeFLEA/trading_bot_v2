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

    @property
    def sector_map(self) -> Dict[str, str]:
        return dict(self._subindustry_cache)

    def get_data(self) -> Dict[str, Dict]:
        result = {}
        try:
            data = yf.download(
                self._symbols,
                period=self._period,
                interval=self._interval,
                group_by="ticker",
                threads=True,
                progress=False
            )

            if data.empty:
                logging.warning("No data received from yfinance download")
                return result

            # Single ticker case: yfinance returns flat DataFrame
            if len(self._symbols) == 1:
                symbol = self._symbols[0]
                clean = data[["Open", "High", "Low", "Close", "Volume"]].dropna()
                if len(clean) == 0:
                    logging.warning(f"No data for {symbol}, skipping")
                    return result

                result[symbol] = {
                    "price": clean["Close"].iloc[-1],
                    "closes": clean["Close"].tolist(),
                    "opens": clean["Open"].tolist(),
                    "highs": clean["High"].tolist(),
                    "lows": clean["Low"].tolist(),
                    "volumes": clean["Volume"].tolist(),
                    "timestamps": (
                        clean.index.tz_localize("UTC").tolist()
                        if clean.index.tzinfo is None
                        else clean.index.tz_convert("UTC").tolist()
                    ),
                    "subindustry": self._subindustry_cache.get(symbol, "Unknown")
                }
                return result

            # Multi-ticker case: DataFrame has MultiIndex (ticker, column)
            for symbol in self._symbols:
                try:
                    if symbol not in data.columns.levels[0]:
                        logging.warning(f"No data received for {symbol}, skipping")
                        continue

                    ticker_data = data[symbol]
                    clean = ticker_data[["Open", "High", "Low", "Close", "Volume"]].dropna()
                    if len(clean) == 0:
                        logging.warning(f"No data for {symbol}, skipping")
                        continue

                    result[symbol] = {
                        "price": clean["Close"].iloc[-1],
                        "closes": clean["Close"].tolist(),
                        "opens": clean["Open"].tolist(),
                        "highs": clean["High"].tolist(),
                        "lows": clean["Low"].tolist(),
                        "volumes": clean["Volume"].tolist(),
                        "timestamps": (
                            clean.index.tz_localize("UTC").tolist()
                            if clean.index.tzinfo is None
                            else clean.index.tz_convert("UTC").tolist()
                        ),
                        "subindustry": self._subindustry_cache.get(symbol, "Unknown")
                    }
                except Exception as e:
                    logging.warning(f"Error processing data for {symbol}: {e}")
                    continue

        except Exception as e:
            logging.warning(f"Error fetching data via yf.download: {e}")

        return result
