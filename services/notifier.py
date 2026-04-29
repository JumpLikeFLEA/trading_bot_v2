from abc import ABC, abstractmethod

from core.models import Order


class Notifier(ABC):
    @abstractmethod
    def notify(self, message: str) -> None:
        """Send a general notification message."""
        ...

    @abstractmethod
    def notify_order(self, order: Order) -> None:
        """Notify about an order event."""
        ...

    @abstractmethod
    def notify_error(self, error: str) -> None:
        """Notify about an engine error."""
        ...
