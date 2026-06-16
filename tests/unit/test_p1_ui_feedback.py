"""Unit tests for P1 UI feedback behavior."""

from types import SimpleNamespace

from easiflux_desktop.core.event_bus import EventBus
from easiflux_desktop.core.state_store import StateStore
from easiflux_desktop.widgets.order_panel import OrderPanel
from easiflux_desktop.widgets.order_table import OrderTable


class FakeConfigManager:
    def __init__(self):
        self.config = SimpleNamespace(active_symbol="BTCUSDT", active_account_id="default")


class FakeCommandBus:
    def __init__(self):
        self.commands = []

    async def execute(self, command):
        self.commands.append(command)
        return SimpleNamespace(success=True, data=[], error=None)


def _ctx():
    event_bus = EventBus()
    config_manager = FakeConfigManager()
    return SimpleNamespace(
        event_bus=event_bus,
        command_bus=FakeCommandBus(),
        config_manager=config_manager,
        state_store=StateStore(
            event_bus,
            active_symbol=config_manager.config.active_symbol,
            active_account_id=config_manager.config.active_account_id,
        ),
    )


def test_order_panel_cancelled_confirmation_does_not_dispatch(qapp):
    ctx = _ctx()
    panel = OrderPanel(ctx)
    panel._confirm_order = lambda request: False

    panel._on_submit()
    qapp.processEvents()

    assert panel._status.text() == "已取消下单"
    assert ctx.command_bus.commands == []


def test_order_table_busy_state_disables_refresh(qapp):
    table = OrderTable(_ctx())

    table._set_busy(True, "订单状态: 刷新中...")
    assert not table._refresh_btn.isEnabled()
    assert table._status.text() == "订单状态: 刷新中..."

    table._set_busy(False)
    assert table._refresh_btn.isEnabled()
