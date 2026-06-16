"""Unit tests for settings view save behavior."""

from types import SimpleNamespace

from easiflux_desktop.core.commands import SaveConnectionSettingsCommand
from easiflux_desktop.core.event_bus import EventBus
from easiflux_desktop.core.state_store import StateStore
from easiflux_desktop.views.settings_view import SettingsView


class FakeConfigManager:
    def __init__(self):
        self.config = SimpleNamespace(
            active_account_id="default",
            active_symbol="BTCUSDT",
            kline_interval="1",
            use_websocket=True,
        )

    def get_credentials(self):
        return None


class FakeCommandBus:
    def __init__(self):
        self.commands = []

    def execute_background(self, command, on_complete=None):
        self.commands.append(command)
        if on_complete:
            on_complete(SimpleNamespace(success=True, data=SimpleNamespace(), error=None))


def _ctx():
    event_bus = EventBus()
    config_manager = FakeConfigManager()
    return SimpleNamespace(
        config_manager=config_manager,
        command_bus=FakeCommandBus(),
        event_bus=event_bus,
        state_store=StateStore(
            event_bus,
            active_symbol=config_manager.config.active_symbol,
            active_account_id=config_manager.config.active_account_id,
        ),
    )


def test_settings_save_without_credentials_only_saves_config(qapp):
    ctx = _ctx()
    view = SettingsView(ctx)

    view._symbol.setText("ETHUSDT")

    assert view._on_save()
    assert ctx.command_bus.commands
    command = ctx.command_bus.commands[-1]
    assert isinstance(command, SaveConnectionSettingsCommand)
    assert command.active_symbol == "ETHUSDT"
    assert command.credential is None
    assert view._status.text() == "配置已保存"


def test_settings_busy_state_disables_actions(qapp):
    ctx = _ctx()
    view = SettingsView(ctx)

    view._set_busy(True, "连接中...")
    assert not view._save_btn.isEnabled()
    assert not view._test_btn.isEnabled()
    assert not view._connect_btn.isEnabled()
    assert view._status.text() == "连接中..."

    view._set_busy(False)
    assert view._save_btn.isEnabled()
    assert view._test_btn.isEnabled()
    assert view._connect_btn.isEnabled()
