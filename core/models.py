from dataclasses import dataclass
from enum import Enum


class SignalType(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class Signal:
    symbol: str
    type: SignalType
    strength: float = 1.0


@dataclass
class Order:
    symbol: str
    side: str
    quantity: float
    price: float = 0.0


@dataclass
class Position:
    symbol: str
    quantity: float
    entry_price: float
