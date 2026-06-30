"""Integration tests for application startup."""

from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QMainWindow, QWidget
from qasync import QEventLoop

from easiflux_desktop.core.context import AppContext
from easiflux_desktop.views.main_window import MainWindow

_VIEW_NAMES = (
    "MarketView",
    "TradingView",
    "AccountView",
    "AnalyticsView",
    "SettingsView",
    "ConnectionStatusWidget",
)


@pytest.fixture
def stub_widget(qapp):
    return QWidget()


@pytest.fixture
def stub_main_window_views(stub_widget, monkeypatch):
    for name in _VIEW_NAMES:
        monkeypatch.setattr(
            f"easiflux_desktop.views.main_window.{name}",
            lambda *args, widget=stub_widget, **kwargs: widget,
        )


@pytest.fixture
def event_loop(qapp):
    loop = QEventLoop(qapp)
    asyncio.set_event_loop(loop)
    yield loop


def test_main_window_defers_auto_connect_before_loop_runs(
    qapp,
    stub_main_window_views,
    monkeypatch,
):
    ctx = AppContext.create()
    scheduled_callbacks: list[object] = []

    def fake_single_shot(_delay, callback):
        scheduled_callbacks.append(callback)

    monkeypatch.setattr("easiflux_desktop.views.main_window.QTimer.singleShot", fake_single_shot)

    with patch.object(ctx.config_manager, "has_credentials", return_value=True):
        window = MainWindow(ctx)

    assert len(scheduled_callbacks) == 1
    assert scheduled_callbacks[0] == window._schedule_auto_connect


def test_schedule_auto_connect_with_running_loop(qapp, event_loop):
    ctx = AppContext.create()
    window = MainWindow.__new__(MainWindow)
    QMainWindow.__init__(window)
    window._ctx = ctx
    called: list[bool] = []

    async def _fake_auto_connect() -> None:
        called.append(True)

    window._auto_connect = _fake_auto_connect  # type: ignore[method-assign]

    async def _run() -> None:
        window._schedule_auto_connect()
        await asyncio.sleep(0)

    with event_loop:
        event_loop.run_until_complete(_run())

    assert called
