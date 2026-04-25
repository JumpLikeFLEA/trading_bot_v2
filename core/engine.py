from typing import Any, List, Optional, Protocol

from adapters.broker import Broker
from core.models import Order
from core.strategy import Strategy
from services.risk_manager import RiskManager


class DataFeed(Protocol):
    def get_data(self) -> Any:
        ...


class Metrics(Protocol):
    def record_trade(self, order: Order) -> None:
        ...


class Engine:
    def __init__(
        self,
        broker: Broker,
        strategies: List[Strategy],
        risk_manager: RiskManager,
        data_feed: DataFeed,
        metrics: Metrics
    ):
        self.broker = broker
        self.strategies = strategies
        self.risk_manager = risk_manager
        self.data_feed = data_feed
        self.metrics = metrics

    def run(self) -> None:
        while True:
            data = self.data_feed.get_data()
            balance = self.broker.get_balance()

            for strategy in self.strategies:
                signal = strategy.on_data(data)
                order = self.risk_manager.evaluate(signal, balance)

                if order is not None:
                    self.broker.place_order(order)
                    self.metrics.record_trade(order)
