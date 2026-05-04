#!/usr/bin/env python3
"""Fetch and validate a stock universe from Wikipedia, then write valid tickers to universes/{universe}.json."""

import argparse
import io
import json
import logging
from pathlib import Path

import pandas as pd
import requests
import yfinance as yf

SOURCES = {
    "sp500":     ("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies", 0, "Symbol"),
    "nasdaq100": ("https://en.wikipedia.org/wiki/Nasdaq-100",                  4, "Ticker"),
    "dowjones":  ("https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average", 1, "Symbol"),
}

ROOT = Path(__file__).resolve().parent.parent


def fetch_symbols(universe: str) -> list[str]:
    url, table_index, column = SOURCES[universe]
    logging.info(f"Fetching {universe} constituents from Wikipedia...")
    headers = {"User-Agent": "Mozilla/5.0 (compatible; trading-bot-universe-updater/1.0)"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    tables = pd.read_html(io.StringIO(response.text))
    symbols = tables[table_index][column].str.strip().tolist()
    logging.info(f"Fetched {len(symbols)} symbols from Wikipedia")
    return symbols


def validate_symbol(symbol: str) -> bool:
    try:
        info = yf.Ticker(symbol).info
        return bool(info)
    except Exception:
        return False


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="Update a stock universe from Wikipedia")
    parser.add_argument("--universe", required=True, choices=list(SOURCES), help="Universe to update")
    args = parser.parse_args()

    symbols = fetch_symbols(args.universe)

    valid: list[str] = []
    dropped: list[str] = []

    for symbol in symbols:
        logging.info(f"Validating {symbol}...")
        if validate_symbol(symbol):
            valid.append(symbol)
        else:
            logging.warning(f"Validation failed for {symbol}, dropping")
            dropped.append(symbol)

    output_path = ROOT / "universes" / f"{args.universe}.json"
    with open(output_path, "w") as f:
        json.dump(valid, f, indent=2)
    logging.info(f"Wrote {len(valid)} tickers to {output_path}")

    logging.info(
        f"Summary — fetched: {len(symbols)}, passed: {len(valid)}, "
        f"dropped: {len(dropped)}"
        + (f" ({', '.join(dropped)})" if dropped else "")
    )


if __name__ == "__main__":
    main()
