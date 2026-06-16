"""Main application window."""

from __future__ import annotations

import asyncio

from PySide6.QtWidgets import QMainWindow, QStatusBar, QTabWidget

from easiflux_desktop.core.commands import ConnectCommand
from easiflux_desktop.core.constants import APP_NAME
from easiflux_desktop.core.context import AppContext
from easiflux_desktop.views.account_view import AccountView
from easiflux_desktop.views.analytics_view import AnalyticsView
from easiflux_desktop.views.market_view import MarketView
from easiflux_desktop.views.settings_view import SettingsView
from easiflux_desktop.views.trading_view import TradingView
from easiflux_desktop.widgets.connection_status import ConnectionStatusWidget


class MainWindow(QMainWindow):
    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self._ctx = ctx
        config = ctx.config_manager.config
        self.setWindowTitle(APP_NAME)
        self.resize(config.window_width, config.window_height)

        tabs = QTabWidget()
        tabs.addTab(MarketView(ctx), "行情")
        tabs.addTab(TradingView(ctx), "交易")
        tabs.addTab(AccountView(ctx), "账户")
        tabs.addTab(AnalyticsView(ctx), "分析")
        tabs.addTab(SettingsView(ctx), "设置")
        self.setCentralWidget(tabs)

        status = QStatusBar()
        status.addPermanentWidget(ConnectionStatusWidget(ctx))
        self.setStatusBar(status)

        ctx.event_bus.subscribe("error.occurred", self._on_error)

        if ctx.config_manager.has_credentials():
            asyncio.create_task(self._auto_connect())

    async def _auto_connect(self) -> None:
        try:
            await self._ctx.command_bus.execute(ConnectCommand())
        except Exception:
            pass

    def _on_error(self, error) -> None:
        self.statusBar().showMessage(str(error.user_message), 5000)

    def closeEvent(self, event) -> None:
        config = self._ctx.config_manager.config
        config.window_width = self.width()
        config.window_height = self.height()
        self._ctx.config_manager.save_config()
        asyncio.create_task(self._ctx.shutdown())
        super().closeEvent(event)
