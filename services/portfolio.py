from typing import Dict, List

from core.models import Position


class Portfolio:
    def __init__(self):
        self._positions: Dict[str, Position] = {}

    def update(self, positions: List[Position]) -> None:
        self._positions.clear()
        for position in positions:
            self._positions[position.symbol] = position

    def get_position(self, symbol: str) -> Position:
        return self._positions.get(symbol)

    def get_all_positions(self) -> List[Position]:
        return list(self._positions.values())
