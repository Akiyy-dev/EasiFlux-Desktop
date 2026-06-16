"""Unit tests for P2 analytics console behavior."""

from decimal import Decimal
from types import SimpleNamespace

import pytest

from easiflux_desktop.core.event_bus import EventBus
from easiflux_desktop.services.risk_manager import RiskConfig
from easiflux_desktop.views.analytics_view import AnalyticsView


class FakeAnalyticsService:
    def compute_stats(self):
        return SimpleNamespace(
            total_orders=0,
            filled_orders=0,
            total_pnl=Decimal("0"),
            win_count=0,
            loss_count=0,
        )


class FakeStrategyManager:
    def __init__(self):
        self.enabled = False

    def list_strategies(self):
        return [SimpleNamespace(name="grid", enabled=self.enabled)]


class FakeCommandBus:
    def __init__(self, strategy_manager):
        self.strategy_manager = strategy_manager
        self.commands = []

    async def execute(self, command):
        self.commands.append(command)
        if command.__class__.__name__ == "ExportAnalyticsCommand":
            return SimpleNamespace(success=True, data="/tmp/orders.csv", error=None)
        if command.__class__.__name__ == "ToggleStrategyCommand":
            self.strategy_manager.enabled = command.enabled
            return SimpleNamespace(success=True, data=self.strategy_manager.list_strategies(), error=None)
        return SimpleNamespace(success=True, data=command, error=None)


def _ctx():
    strategy_manager = FakeStrategyManager()
    return SimpleNamespace(
        event_bus=EventBus(),
        analytics_service=FakeAnalyticsService(),
        risk_manager=SimpleNamespace(config=RiskConfig()),
        strategy_manager=strategy_manager,
        command_bus=FakeCommandBus(strategy_manager),
    )


def test_analytics_view_builds_valid_risk_config(qapp):
    view = AnalyticsView(_ctx())
    view._risk_enabled.setChecked(False)
    view._max_qty.setText("2.5")
    view._max_price_deviation.setText("3.5")
    view._max_daily_orders.setText("25")

    risk_config = view._build_risk_config()

    assert risk_config is not None
    assert not risk_config.enabled
    assert risk_config.max_order_qty == Decimal("2.5")
    assert risk_config.max_price_deviation_pct == Decimal("3.5")
    assert risk_config.max_daily_orders == 25


def test_analytics_view_rejects_invalid_risk_config(qapp):
    view = AnalyticsView(_ctx())
    view._max_qty.setText("bad")

    assert view._build_risk_config() is None
    assert view._risk_status.text() == "风控保存失败: 参数格式无效"


@pytest.mark.asyncio
async def test_analytics_view_exports_and_toggles_strategy(qapp):
    ctx = _ctx()
    view = AnalyticsView(ctx)

    await view._export_orders()
    await view._toggle_strategy("grid")

    assert view._export_status.text() == "导出状态: /tmp/orders.csv"
    assert ctx.strategy_manager.enabled
    label, button = view._strategy_rows["grid"]
    assert label.text() == "grid: 启用"
    assert button.text() == "停用"
