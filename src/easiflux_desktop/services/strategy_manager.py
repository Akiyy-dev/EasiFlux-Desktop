"""Strategy engine with pluggable strategy interface."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from easiflux_desktop.core.event_bus import EventBus
from easiflux_desktop.models.market import DesktopTicker
from easiflux_desktop.models.trading import PlaceOrderRequest

logger = logging.getLogger(__name__)


class Strategy(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    async def on_ticker(self, ticker: DesktopTicker) -> PlaceOrderRequest | None:
        ...


@dataclass
class StrategyState:
    name: str
    enabled: bool = False
    params: dict[str, Any] = field(default_factory=dict)


class GridStrategy(Strategy):
    def __init__(self, symbol: str, grid_price: str, qty: str) -> None:
        self._symbol = symbol
        self._grid_price = grid_price
        self._qty = qty

    @property
    def name(self) -> str:
        return "grid"

    async def on_ticker(self, ticker: DesktopTicker) -> PlaceOrderRequest | None:
        return None


class StrategyManager:
    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus
        self._strategies: dict[str, Strategy] = {}
        self._states: dict[str, StrategyState] = {}
        self._enabled = False
        event_bus.subscribe("ticker.updated", self._on_ticker)

    def register(self, strategy: Strategy) -> None:
        self._strategies[strategy.name] = strategy
        self._states[strategy.name] = StrategyState(name=strategy.name)

    def enable(self, name: str) -> None:
        if name in self._states:
            self._states[name].enabled = True
            self._enabled = True
            logger.info("Strategy enabled: %s", name)

    def disable(self, name: str) -> None:
        if name in self._states:
            self._states[name].enabled = False
        self._enabled = any(s.enabled for s in self._states.values())

    def disable_all(self) -> None:
        for state in self._states.values():
            state.enabled = False
        self._enabled = False

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    def list_strategies(self) -> list[StrategyState]:
        return list(self._states.values())

    def _on_ticker(self, ticker: DesktopTicker) -> None:
        if not self._enabled:
            return
        import asyncio

        async def _run() -> None:
            for name, strategy in self._strategies.items():
                state = self._states.get(name)
                if not state or not state.enabled:
                    continue
                signal = await strategy.on_ticker(ticker)
                if signal:
                    self._event_bus.publish("strategy.signal", signal)

        asyncio.create_task(_run())
