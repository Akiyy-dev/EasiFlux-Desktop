"""Unit tests for WebSocket adapter subscription recovery."""

import pytest

from easiflux_desktop.adapters.ws_adapter import WsAdapter
from easiflux_desktop.core.event_bus import EventBus


class FakeWs:
    def __init__(self):
        self.connect_count = 0
        self.close_count = 0
        self.subscriptions = []

    async def connect(self):
        self.connect_count += 1

    async def close(self):
        self.close_count += 1

    async def subscribe(self, channel, params, callback=None):
        self.subscriptions.append((channel, params, callback))


class FakeClient:
    def __init__(self):
        self.ws = FakeWs()


class FakeFactory:
    def __init__(self):
        self.client = FakeClient()

    def require_client(self):
        return self.client


@pytest.mark.asyncio
async def test_ws_adapter_reconnect_resubscribes(qapp):
    bus = EventBus()
    statuses = []
    bus.subscribe("websocket.status_changed", statuses.append)
    factory = FakeFactory()
    adapter = WsAdapter(factory, bus)

    await adapter.subscribe_all("BTCUSDT")
    qapp.processEvents()

    assert adapter.is_active
    assert adapter.subscription_count == 5
    assert factory.client.ws.connect_count == 1
    assert len(factory.client.ws.subscriptions) == 5
    assert statuses == ["connected"]

    await adapter.reconnect()
    qapp.processEvents()

    assert adapter.is_active
    assert adapter.subscription_count == 5
    assert factory.client.ws.close_count == 1
    assert factory.client.ws.connect_count == 2
    assert len(factory.client.ws.subscriptions) == 10
    assert statuses[-2:] == ["disconnected", "connected"]


@pytest.mark.asyncio
async def test_ws_adapter_stop_clears_subscriptions():
    adapter = WsAdapter(FakeFactory(), EventBus())

    await adapter.subscribe_ticker("BTCUSDT")
    await adapter.stop()

    assert not adapter.is_active
    assert adapter.subscription_count == 0
