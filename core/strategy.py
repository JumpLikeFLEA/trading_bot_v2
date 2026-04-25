from abc import ABC, abstractmethod
from typing import Any

from .models import Signal


class Strategy(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def on_data(self, data: Any) -> Signal:
        pass
