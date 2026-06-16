"""WebSocket adapter bridging SDK WS to EventBus."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from easiflux_desktop.adapters.model_mapper import ModelMapper
from easiflux_desktop.adapters.sdk_client_factory import SdkClientFactory
from easiflux_desktop.core.event_bus import EventBus

logger = logging.getLogger(__name__)


@dataclass
class WsSubscription:
    channel: str
    params: dict[str, Any] = field(default_factory=dict)
    handler: Callable[[dict[str, Any]], Awaitable[None]] | None = None


class WsAdapter:
    def __init__(self, factory: SdkClientFactory, event_bus: EventBus) -> None:
        self._factory = factory
        self._event_bus = event_bus
        self._active_symbol: str | None = None
        self._started = False
        self._subscriptions: dict[tuple[str, tuple[tuple[str, Any], ...]], WsSubscription] = {}

    @property
    def is_active(self) -> bool:
        return self._started

    @property
    def subscription_count(self) -> int:
        return len(self._subscriptions)

    async def start(self) -> None:
        client = self._factory.require_client()
        if not self._started:
            await client.ws.connect()
            self._started = True
            self._event_bus.publish("websocket.status_changed", "connected", sticky=True)
            logger.info("WebSocket connected")

    async def stop(self, *, forget_subscriptions: bool = True) -> None:
        if self._started:
            client = self._factory.client
            if client:
                await client.ws.close()
            self._started = False
            self._active_symbol = None
            self._event_bus.publish("websocket.status_changed", "disconnected", sticky=True)
        if forget_subscriptions:
            self._subscriptions.clear()

    async def reconnect(self) -> None:
        subscriptions = list(self._subscriptions.values())
        await self.stop(forget_subscriptions=False)
        await self.start()
        for subscription in subscriptions:
            await self._subscribe_now(subscription)
        logger.info("WebSocket reconnected with %s subscriptions", len(subscriptions))

    async def subscribe_ticker(self, symbol: str) -> None:
        self._active_symbol = symbol

        async def _on_message(message: dict[str, Any]) -> None:
            try:
                data = message.get("data") or message
                if isinstance(data, dict):
                    ticker = ModelMapper.to_desktop_ticker(data, symbol=symbol)
                    self._event_bus.publish("ticker.updated", ticker)
            except Exception as exc:
                logger.debug("Ticker WS parse error: %s", exc)

        await self._remember_and_subscribe("ticker", {"symbol": symbol}, _on_message)

    async def subscribe_depth(self, symbol: str, *, limit: int = 20) -> None:
        async def _on_message(message: dict[str, Any]) -> None:
            try:
                depth = ModelMapper.depth_from_payload(message, symbol)
                self._event_bus.publish("depth.updated", depth)
            except Exception as exc:
                logger.debug("Depth WS parse error: %s", exc)

        await self._remember_and_subscribe("depth", {"symbol": symbol, "depth": limit}, _on_message)

    async def subscribe_orders(self) -> None:
        await self._subscribe_private("order", self._on_order)

    async def subscribe_positions(self) -> None:
        await self._subscribe_private("position", self._on_position)

    async def subscribe_balances(self) -> None:
        await self._subscribe_private("balance", self._on_balance)

    async def subscribe_all(self, symbol: str) -> None:
        await self.subscribe_ticker(symbol)
        await self.subscribe_depth(symbol)
        await self.subscribe_orders()
        await self.subscribe_positions()
        await self.subscribe_balances()

    async def _subscribe_private(self, channel: str, handler: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
        await self._remember_and_subscribe(channel, {}, handler)

    async def _remember_and_subscribe(
        self,
        channel: str,
        params: dict[str, Any],
        handler: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        await self.start()
        subscription = WsSubscription(channel=channel, params=dict(params), handler=handler)
        self._subscriptions[self._subscription_key(channel, params)] = subscription
        await self._subscribe_now(subscription)

    async def _subscribe_now(self, subscription: WsSubscription) -> None:
        client = self._factory.require_client()
        await client.ws.subscribe(
            subscription.channel,
            dict(subscription.params),
            callback=subscription.handler,
        )

    @staticmethod
    def _subscription_key(channel: str, params: dict[str, Any]) -> tuple[str, tuple[tuple[str, Any], ...]]:
        return channel, tuple(sorted(params.items()))

    async def _on_order(self, message: dict[str, Any]) -> None:
        try:
            data = message.get("data") or message
            if isinstance(data, list):
                for item in data:
                    order = ModelMapper.to_desktop_order(item)
                    self._event_bus.publish("order.updated", order)
                    if order.status.value == "Filled":
                        self._event_bus.publish("order.filled", order)
            elif isinstance(data, dict):
                order = ModelMapper.to_desktop_order(data)
                self._event_bus.publish("order.updated", order)
                if order.status.value == "Filled":
                    self._event_bus.publish("order.filled", order)
        except Exception as exc:
            logger.debug("Order WS parse error: %s", exc)

    async def _on_position(self, message: dict[str, Any]) -> None:
        try:
            data = message.get("data") or message
            if isinstance(data, list):
                for item in data:
                    self._event_bus.publish("position.updated", ModelMapper.to_desktop_position(item))
            elif isinstance(data, dict):
                self._event_bus.publish("position.updated", ModelMapper.to_desktop_position(data))
        except Exception as exc:
            logger.debug("Position WS parse error: %s", exc)

    async def _on_balance(self, message: dict[str, Any]) -> None:
        try:
            data = message.get("data") or message
            if isinstance(data, list):
                for item in data:
                    self._event_bus.publish("balance.updated", ModelMapper.to_desktop_balance(item))
            elif isinstance(data, dict):
                self._event_bus.publish("balance.updated", ModelMapper.to_desktop_balance(data))
        except Exception as exc:
            logger.debug("Balance WS parse error: %s", exc)
