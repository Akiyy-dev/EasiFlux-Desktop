"""Integration tests for application startup."""

from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QMainWindow
from qasync import QEventLoop

from easiflux_desktop.core.context import AppContext
from easiflux_desktop.views.main_window import MainWindow


@pytest.fixture
def event_loop(qapp):
    loop = QEventLoop(qapp)
    asyncio.set_event_loop(loop)
    yield loop


def test_main_window_init_with_credentials_before_loop_runs(qapp, qtbot, event_loop):
    ctx = AppContext.create()

    with patch.object(ctx.config_manager, "has_credentials", return_value=True):
        window = MainWindow(ctx)
        window.show()

    qtbot.addWidget(window)
    assert window.isVisible()


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
