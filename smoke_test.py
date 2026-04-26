"""Standalone smoke test script for market data and RSI signals."""

import argparse
import sys
from typing import Dict, List, Optional, Tuple

import yfinance as yf

from core.models import Signal, SignalType


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Market data smoke test with RSI signals")
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=["AAPL", "MSFT", "GOOGL", "AMZN"],
        help="Space-separated list of ticker symbols"
    )
    parser.add_argument(
        "--period",
        choices=["1y", "1mo", "1wk", "1d"],
        default="1mo",
        help="Data period"
    )
    parser.add_argument(
        "--interval",
        choices=["1d", "1h", "15m"],
        default="1d",
        help="Data interval"
    )
    return parser.parse_args()


def calculate_rsi(prices: List[float], period: int = 14) -> float:
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
    return 100 - (100 / (1 + rs))


def calculate_sma(prices: List[float], period: int) -> Optional[float]:
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period


def get_signal(rsi: float) -> SignalType:
    if rsi < 30:
        return SignalType.BUY
    elif rsi > 70:
        return SignalType.SELL
    else:
        return SignalType.HOLD


def analyze_symbol(symbol: str, period: str, interval: str) -> Optional[Dict]:
    try:
        ticker = yf.Ticker(symbol)

        # Get data for the selected period
        hist = ticker.history(period=period, interval=interval)
        if len(hist) == 0:
            print(f"Warning: No data for {symbol}", file=sys.stderr)
            return None

        closes = hist["Close"].tolist()
        current_price = closes[-1]

        # Calculate RSI
        rsi = calculate_rsi(closes)

        # Calculate SMAs
        sma_20 = calculate_sma(closes, 20)
        sma_50 = calculate_sma(closes, 50)

        # Get 52-week high/low (or full range for shorter periods)
        if period == "1y":
            high_52w = max(hist["High"])
            low_52w = min(hist["Low"])
        else:
            # For shorter periods, get the 1y data separately
            yearly_hist = ticker.history(period="1y", interval="1d")
            if len(yearly_hist) > 0:
                high_52w = max(yearly_hist["High"])
                low_52w = min(yearly_hist["Low"])
            else:
                high_52w = max(hist["High"])
                low_52w = min(hist["Low"])

        # Average volume (daily)
        if "Volume" in hist.columns:
            avg_volume = hist["Volume"].mean()
        else:
            avg_volume = 0

        # Price change % over period
        price_change_pct = ((closes[-1] - closes[0]) / closes[0]) * 100

        # Signal
        signal_type = get_signal(rsi)

        return {
            "symbol": symbol,
            "price": current_price,
            "rsi": rsi,
            "high_52w": high_52w,
            "low_52w": low_52w,
            "sma_20": sma_20,
            "sma_50": sma_50,
            "avg_volume": avg_volume,
            "price_change_pct": price_change_pct,
            "signal": signal_type,
        }

    except Exception as e:
        print(f"Warning: Error analyzing {symbol}: {e}", file=sys.stderr)
        return None


def print_report(data: Dict) -> None:
    print(f"\n{'=' * 50}")
    print(f"Symbol: {data['symbol']}")
    print(f"{'=' * 50}")
    print(f"Current Price:        ${data['price']:.2f}")
    print(f"RSI (14):              {data['rsi']:.2f}")
    print(f"52-Week High:          ${data['high_52w']:.2f}")
    print(f"52-Week Low:           ${data['low_52w']:.2f}")

    sma_20_str = f"${data['sma_20']:.2f}" if data['sma_20'] else "N/A"
    sma_50_str = f"${data['sma_50']:.2f}" if data['sma_50'] else "N/A"
    print(f"SMA 20:                {sma_20_str}")
    print(f"SMA 50:                {sma_50_str}")

    print(f"Avg Daily Volume:      {data['avg_volume']:,.0f}")
    print(f"Price Change ({args.period}):    {data['price_change_pct']:+.2f}%")
    print(f"RSI Signal:            {data['signal'].value.upper()}")
    print(f"{'=' * 50}")


def main() -> None:
    global args
    args = parse_args()

    results: List[Dict] = []
    signal_counts = {"BUY": 0, "SELL": 0, "HOLD": 0}

    for symbol in args.symbols:
        data = analyze_symbol(symbol, args.period, args.interval)
        if data:
            print_report(data)
            results.append(data)
            signal_counts[data["signal"].value.upper()] += 1

    print(f"\n{'=' * 50}")
    print("SUMMARY")
    print(f"{'=' * 50}")
    print(f"Symbols analyzed:      {len(results)}")
    print(f"BUY signals:           {signal_counts['BUY']}")
    print(f"SELL signals:          {signal_counts['SELL']}")
    print(f"HOLD signals:          {signal_counts['HOLD']}")
    print(f"{'=' * 50}\n")


if __name__ == "__main__":
    main()
