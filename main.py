from adapters import Trading212Broker
from core import Engine
from services import DataFeed, Metrics, Portfolio, RiskManager, load_secrets
from strategies import RSIStrategy
from ui import Dashboard


def main():
    secrets = load_secrets("secrets/secrets.json")

    broker = Trading212Broker(
        api_key=secrets["api_key"],
        secret=secrets["secret"]
    )

    data_feed = DataFeed()
    metrics = Metrics()
    portfolio = Portfolio()
    risk_manager = RiskManager(portfolio=portfolio)
    strategies = [RSIStrategy(symbol="AAPL")]

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
