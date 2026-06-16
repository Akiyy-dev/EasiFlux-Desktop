"""Central in-memory state store for desktop data."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from easiflux_desktop.core.event_bus import EventBus
from easiflux_desktop.models.account import DesktopBalance
from easiflux_desktop.models.config import ConnectionStatus
from easiflux_desktop.models.market import DesktopDepth, DesktopKline, DesktopTicker
from easiflux_desktop.models.trading import DesktopOrder, DesktopPosition


@dataclass
class MarketState:
    active_symbol: str
    tickers: dict[str, DesktopTicker] = field(default_factory=dict)
    depths: dict[str, DesktopDepth] = field(default_factory=dict)
    klines: dict[tuple[str, str], list[DesktopKline]] = field(default_factory=dict)

    def ticker(self, symbol: str | None = None) -> DesktopTicker | None:
        return self.tickers.get(symbol or self.active_symbol)

    def depth(self, symbol: str | None = None) -> DesktopDepth | None:
        return self.depths.get(symbol or self.active_symbol)

    def kline_series(self, symbol: str | None = None, interval: str | None = None) -> list[DesktopKline]:
        if interval is None:
            matches = [items for (sym, _), items in self.klines.items() if sym == (symbol or self.active_symbol)]
            return list(matches[-1]) if matches else []
        return list(self.klines.get((symbol or self.active_symbol, interval), []))


@dataclass
class AccountState:
    active_account_id: str
    connection_status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    balances: dict[str, DesktopBalance] = field(default_factory=dict)

    @property
    def total_equity(self) -> Decimal:
        return sum((balance.equity for balance in self.balances.values()), Decimal("0"))

    def balance_list(self) -> list[DesktopBalance]:
        return list(self.balances.values())


@dataclass
class PositionState:
    positions: dict[tuple[str, str], DesktopPosition] = field(default_factory=dict)

    def position_list(self) -> list[DesktopPosition]:
        return list(self.positions.values())


@dataclass
class OrderState:
    orders: dict[str, DesktopOrder] = field(default_factory=dict)

    def order_list(self) -> list[DesktopOrder]:
        return list(self.orders.values())

    def open_orders(self) -> list[DesktopOrder]:
        return [order for order in self.orders.values() if not order.is_terminal]


class StateStore:
    """Reduces domain events into queryable UI state snapshots."""

    def __init__(self, event_bus: EventBus, *, active_symbol: str, active_account_id: str) -> None:
        self._event_bus = event_bus
        self.market = MarketState(active_symbol=active_symbol)
        self.account = AccountState(active_account_id=active_account_id)
        self.positions = PositionState()
        self.orders = OrderState()
        self._subscribe()

    def set_active_symbol(self, symbol: str) -> None:
        self.market.active_symbol = symbol
        self._event_bus.publish("state.market.updated", self.market)

    def set_active_account(self, account_id: str) -> None:
        self.account.active_account_id = account_id
        self._event_bus.publish("state.account.updated", self.account)

    def _subscribe(self) -> None:
        self._event_bus.subscribe("market.active_symbol_changed", self._on_active_symbol)
        self._event_bus.subscribe("connection.status_changed", self._on_connection_status)
        self._event_bus.subscribe("ticker.updated", self._on_ticker)
        self._event_bus.subscribe("depth.updated", self._on_depth)
        self._event_bus.subscribe("kline.updated", self._on_kline)
        self._event_bus.subscribe("klines.loaded", self._on_klines_loaded)
        self._event_bus.subscribe("balance.updated", self._on_balance)
        self._event_bus.subscribe("balances.loaded", self._on_balances_loaded)
        self._event_bus.subscribe("position.updated", self._on_position)
        self._event_bus.subscribe("positions.loaded", self._on_positions_loaded)
        self._event_bus.subscribe("order.created", self._on_order)
        self._event_bus.subscribe("order.updated", self._on_order)
        self._event_bus.subscribe("orders.loaded", self._on_orders_loaded)

    def _on_active_symbol(self, symbol: str) -> None:
        self.set_active_symbol(symbol)

    def _on_connection_status(self, status: ConnectionStatus) -> None:
        self.account.connection_status = status
        self._event_bus.publish("state.connection.updated", status, sticky=True)
        self._event_bus.publish("state.account.updated", self.account)

    def _on_ticker(self, ticker: DesktopTicker) -> None:
        self.market.tickers[ticker.symbol] = ticker
        self._event_bus.publish("state.market.updated", self.market)

    def _on_depth(self, depth: DesktopDepth) -> None:
        self.market.depths[depth.symbol] = depth
        self._event_bus.publish("state.market.updated", self.market)

    def _on_kline(self, kline: DesktopKline) -> None:
        key = (kline.symbol, kline.interval)
        series = self.market.klines.setdefault(key, [])
        series = [item for item in series if item.timestamp != kline.timestamp]
        series.append(kline)
        series.sort(key=lambda item: item.timestamp)
        self.market.klines[key] = series[-500:]
        self._event_bus.publish("state.klines.updated", self.market)
        self._event_bus.publish("state.market.updated", self.market)

    def _on_klines_loaded(self, payload: dict[str, Any]) -> None:
        symbol = str(payload.get("symbol") or self.market.active_symbol)
        interval = str(payload.get("interval") or "")
        klines = payload.get("klines") or []
        self.market.klines[(symbol, interval)] = list(klines)
        self._event_bus.publish("state.klines.updated", self.market)
        self._event_bus.publish("state.market.updated", self.market)

    def _on_balance(self, balance: DesktopBalance) -> None:
        self.account.balances[balance.coin] = balance
        self._event_bus.publish("state.account.updated", self.account)

    def _on_balances_loaded(self, balances: list[DesktopBalance]) -> None:
        self.account.balances = {balance.coin: balance for balance in balances}
        self._event_bus.publish("state.account.updated", self.account)

    def _on_position(self, position: DesktopPosition) -> None:
        self.positions.positions[(position.symbol, position.side.value)] = position
        self._event_bus.publish("state.positions.updated", self.positions)

    def _on_positions_loaded(self, positions: list[DesktopPosition]) -> None:
        self.positions.positions = {(position.symbol, position.side.value): position for position in positions}
        self._event_bus.publish("state.positions.updated", self.positions)

    def _on_order(self, order: DesktopOrder) -> None:
        self.orders.orders[order.order_id] = order
        self._event_bus.publish("state.orders.updated", self.orders)

    def _on_orders_loaded(self, payload: dict[str, Any]) -> None:
        symbol = payload.get("symbol")
        orders = payload.get("orders") or []
        if symbol:
            self.orders.orders = {
                order_id: order
                for order_id, order in self.orders.orders.items()
                if order.is_terminal or order.symbol != symbol
            }
        else:
            self.orders.orders = {
                order_id: order for order_id, order in self.orders.orders.items() if order.is_terminal
            }
        for order in orders:
            self.orders.orders[order.order_id] = order
        self._event_bus.publish("state.orders.updated", self.orders)
