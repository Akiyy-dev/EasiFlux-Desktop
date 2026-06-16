"""Unit tests for settings view save behavior."""

from types import SimpleNamespace

from easiflux_desktop.views.settings_view import SettingsView


class FakeConfigManager:
    def __init__(self):
        self.config = SimpleNamespace(
            active_account_id="default",
            active_symbol="BTCUSDT",
            use_websocket=True,
        )
        self.saved = False
        self.credentials_saved = False

    def get_credentials(self):
        return None

    def set_credentials(self, account_id, credential):
        self.credentials_saved = True

    def save_config(self):
        self.saved = True


class FakeCommandBus:
    def __init__(self):
        self.commands = []

    def execute_background(self, command):
        self.commands.append(command)


def test_settings_save_without_credentials_only_saves_config(qapp):
    config_manager = FakeConfigManager()
    command_bus = FakeCommandBus()
    ctx = SimpleNamespace(config_manager=config_manager, command_bus=command_bus)
    view = SettingsView(ctx)

    view._symbol.setText("ETHUSDT")

    assert view._on_save()
    assert config_manager.saved
    assert not config_manager.credentials_saved
    assert config_manager.config.active_symbol == "ETHUSDT"
    assert command_bus.commands
