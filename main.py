from adapters import Trading212Broker
from core import Engine
from services import DataFeed, Metrics, RiskManager, load_secrets
from strategies import RSIStrategy


def main():
    secrets = load_secrets("secrets/encrypted.json")

    broker = Trading212Broker(
        api_key=secrets["api_key"],
        secret=secrets["secret"]
    )

    data_feed = DataFeed()
    metrics = Metrics()
    risk_manager = RiskManager()
    strategies = [RSIStrategy()]

    engine = Engine(
        broker=broker,
        strategies=strategies,
        risk_manager=risk_manager,
        data_feed=data_feed,
        metrics=metrics
    )

    engine.run()


if __name__ == "__main__":
    main()
