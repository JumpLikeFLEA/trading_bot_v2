from abc import ABC, abstractmethod
from typing import Any, List

from .models import Signal


class Strategy(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def on_data(self, data: Any) -> List[Signal]:
        pass
