"""Integration test for AppContext wiring."""

from easiflux_desktop.core.context import AppContext


def test_app_context_create():
    ctx = AppContext.create()
    assert ctx.event_bus is not None
    assert ctx.config_manager is not None
    assert ctx.market_manager is not None
    assert ctx.trading_manager is not None
    assert ctx.strategy_manager is not None
    assert ctx.analytics_service is not None
