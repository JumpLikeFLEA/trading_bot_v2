import argparse
import logging
import sys
import threading

from adapters import TelegramListener, TelegramNotifier, Trading212Broker
from core import Engine
from core.strategy_factory import build_strategies
from services import DataFeed, Metrics, Portfolio, RiskManager, load_config, load_secrets
from services.risk_manager import MaxDailyLossRule, MaxSectorExposureRule, MaxSymbolExposureRule, NoDoublePositionRule
from ui import Dashboard


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Trading Bot")
    parser.add_argument(
        "--strategy",
        type=str,
        default=None,
        help="Override config and run only the specified strategy"
    )
    parser.add_argument(
        "--period",
        type=str,
        default=None,
        help="Override data feed period (e.g., 1d, 1wk, 1mo, 3mo, 6mo, 1y)"
    )
    parser.add_argument(
        "--interval",
        type=str,
        default=None,
        help="Override data feed interval (e.g., 15m, 1h, 1d)"
    )
    parser.add_argument(
        "--symbols",
        type=str,
        default=None,
        help="Override symbols list (comma-separated tickers, e.g., 'AAPL,MSFT,GOOGL')"
    )
    return parser.parse_args()


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    args = parse_args()
    config = load_config("config.json")

    # Apply CLI overrides to config
    if args.period is not None:
        config["data_feed"]["period"] = args.period
    if args.interval is not None:
        config["data_feed"]["interval"] = args.interval
    if args.symbols is not None:
        symbols_list = [s.strip() for s in args.symbols.split(",")]
        config["symbols"] = symbols_list
        # Propagate to all strategies so they use the same symbol list
        for strategy_config in config.get("strategies", []):
            strategy_config["symbols"] = symbols_list

    secrets = load_secrets("secrets/secrets.json")

    # Notifier setup
    notifier_config = config.get("notifier", {})
    if notifier_config.get("enabled", False) and notifier_config.get("provider") == "telegram":
        notifier = TelegramNotifier(
            bot_token=secrets["bot_token"],
            chat_id=secrets["chat_id"]
        )
    else:
        notifier = None

    # Control events for Telegram commands
    stop_event = threading.Event()
    pause_event = threading.Event()

    broker = Trading212Broker(
        api_key=secrets["api_key"],
        secret=secrets["secret"],
        live=config.get("live", False)
    )

    data_feed = DataFeed(
        symbols=config["symbols"],
        period=config["data_feed"]["period"],
        interval=config["data_feed"]["interval"]
    )
    metrics = Metrics()
    portfolio = Portfolio()

    risk_config = config.get("risk", {})
    risk_manager = RiskManager(
        portfolio=portfolio,
        rules=[
            NoDoublePositionRule(),
            MaxSymbolExposureRule(max_pct=risk_config.get("max_symbol_exposure_pct", 0.05)),
            MaxSectorExposureRule(
                max_pct=risk_config.get("max_sector_exposure_pct", 0.20),
                sector_map=data_feed.sector_map,
            ),
            MaxDailyLossRule(max_loss_pct=risk_config.get("max_daily_loss_pct", 0.03)),
        ],
        position_size_pct=risk_config.get("position_size_pct", 0.01),
    )
    dashboard = Dashboard(metrics=metrics)

    # Start Telegram listener if notifier is enabled
    if notifier_config.get("enabled", False) and notifier_config.get("provider") == "telegram":
        listener = TelegramListener(
            bot_token=secrets["bot_token"],
            chat_id=secrets["chat_id"],
            stop_event=stop_event,
            pause_event=pause_event,
            dashboard=dashboard,
            notifier=notifier
        )
        threading.Thread(target=listener.start, daemon=True).start()

    # Validate strategy name if provided
    if args.strategy is not None:
        known_strategies = {cfg.get("name") for cfg in config["strategies"]}
        if args.strategy not in known_strategies:
            logging.error(f"Unknown strategy: {args.strategy}")
            sys.exit(1)

    strategies = build_strategies(config["strategies"], strategy_filter=args.strategy)

    engine = Engine(
        broker=broker,
        strategies=strategies,
        risk_manager=risk_manager,
        data_feed=data_feed,
        metrics=metrics,
        portfolio=portfolio,
        dashboard=dashboard,
        notifier=notifier,
        stop_event=stop_event,
        pause_event=pause_event
    )

    engine.run()


if __name__ == "__main__":
    main()
