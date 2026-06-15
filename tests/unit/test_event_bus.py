"""Unit tests for event bus."""

from easiflux_desktop.core.event_bus import EventBus


def test_publish_subscribe(qapp):
    bus = EventBus()
    received = []

    bus.subscribe("ticker.updated", lambda payload: received.append(payload))
    bus.publish("ticker.updated", {"symbol": "BTCUSDT"})
    qapp.processEvents()
    assert received == [{"symbol": "BTCUSDT"}]


def test_sticky_event(qapp):
    bus = EventBus()
    bus.publish("connection.status_changed", "connected", sticky=True)

    received = []
    bus.subscribe("connection.status_changed", lambda payload: received.append(payload))
    qapp.processEvents()
    assert received == ["connected"]
