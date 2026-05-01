import logging
import threading
import time
from typing import Any, List, Optional, Protocol

from core.models import Order
from core.strategy import Strategy
from services.notifier import Notifier
from services.risk_manager import RiskManager
from services.portfolio import Portfolio


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
        broker: Any,
        strategies: List[Strategy],
        risk_manager: RiskManager,
        data_feed: DataFeed,
        metrics: Metrics,
        portfolio: Portfolio,
        interval: int = 60,
        dashboard: Optional[Dashboard] = None,
        stop_event: Optional[threading.Event] = None,
        pause_event: Optional[threading.Event] = None,
        notifier: Optional[Notifier] = None
    ):
        self.broker = broker
        self.strategies = strategies
        self.risk_manager = risk_manager
        self.data_feed = data_feed
        self.metrics = metrics
        self.portfolio = portfolio
        self.interval = interval
        self.dashboard = dashboard
        self.stop_event = stop_event
        self.pause_event = pause_event
        self.notifier = notifier

    def run(self) -> None:
        while True:
            if self.stop_event is not None and self.stop_event.is_set():
                logging.info("Stop signal received, shutting down.")
                return

            if self.pause_event is not None and self.pause_event.is_set():
                logging.info("Bot paused, sleeping.")
                time.sleep(self.interval)
                continue

            try:
                data = self.data_feed.get_data()
                balance = self.broker.get_balance()
                positions = self.broker.get_positions()
                self.portfolio.update(positions)  # needs portfolio passed into Engine

                for strategy in self.strategies:
                    signals = strategy.on_data(data)
                    for symbol, signal_data in data.items():
                        current_price = signal_data["price"]
                        for signal in signals:
                            if signal.symbol != symbol:
                                continue
                            if self.dashboard is not None:
                                self.dashboard.update_signal(symbol, signal.type, current_price)
                            order = self.risk_manager.evaluate(signal, balance, current_price)

                            if order is not None:
                                self.broker.place_order(order)
                                if self.notifier:
                                    self.notifier.notify_order(order)
                                self.metrics.record_trade(order)
                                if self.dashboard is not None:
                                    self.dashboard.update_last_order(order, current_price)

                if self.dashboard is not None:
                    self.dashboard.increment_cycle()
                    self.dashboard._render()

                time.sleep(self.interval)
            except Exception as e:
                logging.exception("Error in engine loop")
                if self.notifier:
                    self.notifier.notify_error(str(e))
                time.sleep(self.interval)
