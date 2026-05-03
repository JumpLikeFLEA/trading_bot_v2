"""Dry run strategy wrapper that always stays active."""

from datetime import datetime
from typing import Any, List

from .models import Position, Signal
from .strategy import Strategy


class DryRunStrategy(Strategy):
    """Wrapper strategy that delegates to another strategy but always reports as active.

    Used for dry-run mode to bypass time-based activation checks.
    """

    def __init__(self, strategy: Strategy):
        self._strategy = strategy

    @property
    def name(self) -> str:
        return self._strategy.name

    def on_data(self, data: Any) -> List[Signal]:
        return self._strategy.on_data(data)

    def on_deactivate(self, positions: List[Position]) -> List[Signal]:
        return self._strategy.on_deactivate(positions)

    def is_active(self, now: datetime) -> bool:
        """Always returns True, ignoring the time argument."""
        return True
