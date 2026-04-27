import argparse
import logging
import sys

from adapters import Trading212Broker
from core import Engine
from core.strategy_factory import build_strategies
from services import DataFeed, Metrics, Portfolio, RiskManager, load_config, load_secrets
from ui import Dashboard


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Trading Bot")
    parser.add_argument(
        "--strategy",
        type=str,
        default=None,
        help="Override config and run only the specified strategy"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    config = load_config("config.json")
    secrets = load_secrets("secrets/secrets.json")

    broker = Trading212Broker(
        api_key=secrets["api_key"],
        secret=secrets["secret"]
    )

    data_feed = DataFeed(
        symbols=config["symbols"],
        period=config["data_feed"]["period"],
        interval=config["data_feed"]["interval"]
    )
    metrics = Metrics()
    portfolio = Portfolio()
    risk_manager = RiskManager(portfolio=portfolio)

    # Validate strategy name if provided
    if args.strategy is not None:
        known_strategies = {cfg.get("name") for cfg in config["strategies"]}
        if args.strategy not in known_strategies:
            logging.error(f"Unknown strategy: {args.strategy}")
            sys.exit(1)

    strategies = build_strategies(config["strategies"], strategy_filter=args.strategy)

    dashboard = Dashboard(metrics=metrics)

    engine = Engine(
        broker=broker,
        strategies=strategies,
        risk_manager=risk_manager,
        data_feed=data_feed,
        metrics=metrics,
        dashboard=dashboard
    )

    engine.run()


if __name__ == "__main__":
    main()
