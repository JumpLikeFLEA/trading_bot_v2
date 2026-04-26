import logging
import time
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


class Dashboard(Protocol):
    def update_last_order(self, order: Order) -> None:
        ...

    def _render(self) -> None:
        ...


class Engine:
    def __init__(
        self,
        broker: Broker,
        strategies: List[Strategy],
        risk_manager: RiskManager,
        data_feed: DataFeed,
        metrics: Metrics,
        interval: int = 60,
        dashboard: Optional[Dashboard] = None
    ):
        self.broker = broker
        self.strategies = strategies
        self.risk_manager = risk_manager
        self.data_feed = data_feed
        self.metrics = metrics
        self.interval = interval
        self.dashboard = dashboard

    def run(self) -> None:
        while True:
            try:
                data = self.data_feed.get_data()
                balance = self.broker.get_balance()

                for strategy in self.strategies:
                    signals = strategy.on_data(data)
                    for symbol, signal_data in data.items():
                        for signal in signals:
                            if signal.symbol != symbol:
                                continue
                            order = self.risk_manager.evaluate(signal, balance, signal_data["price"])

                            if order is not None:
                                self.broker.place_order(order)
                                self.metrics.record_trade(order)
                                if self.dashboard is not None:
                                    self.dashboard.update_last_order(order)

                if self.dashboard is not None:
                    self.dashboard._render()

                time.sleep(self.interval)
            except Exception:
                logging.exception("Error in engine loop")
