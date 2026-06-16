"""Unit tests for settings view save behavior."""

from types import SimpleNamespace

from easiflux_desktop.core.commands import SaveConnectionSettingsCommand
from easiflux_desktop.views.settings_view import SettingsView


class FakeConfigManager:
    def __init__(self):
        self.config = SimpleNamespace(
            active_account_id="default",
            active_symbol="BTCUSDT",
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


def test_settings_save_without_credentials_only_saves_config(qapp):
    config_manager = FakeConfigManager()
    command_bus = FakeCommandBus()
    ctx = SimpleNamespace(config_manager=config_manager, command_bus=command_bus)
    view = SettingsView(ctx)

    view._symbol.setText("ETHUSDT")

    assert view._on_save()
    assert command_bus.commands
    command = command_bus.commands[-1]
    assert isinstance(command, SaveConnectionSettingsCommand)
    assert command.active_symbol == "ETHUSDT"
    assert command.credential is None
    assert view._status.text() == "配置已保存"


def test_settings_busy_state_disables_actions(qapp):
    config_manager = FakeConfigManager()
    command_bus = FakeCommandBus()
    ctx = SimpleNamespace(config_manager=config_manager, command_bus=command_bus)
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
