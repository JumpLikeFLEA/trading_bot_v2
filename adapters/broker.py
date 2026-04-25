from abc import ABC, abstractmethod
from typing import List

from core.models import Order, Position


class Broker(ABC):
    @abstractmethod
    def get_balance(self) -> float:
        pass

    @abstractmethod
    def get_positions(self) -> List[Position]:
        pass

    @abstractmethod
    def place_order(self, order: Order) -> None:
        pass
