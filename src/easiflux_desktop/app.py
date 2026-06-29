"""Application entry point."""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from qasync import QEventLoop

from easiflux_desktop.core.constants import APP_NAME
from easiflux_desktop.core.context import AppContext
from easiflux_desktop.views.main_window import MainWindow

logger = logging.getLogger(__name__)


def _resource_path() -> Path:
    # PyInstaller onefile extracts files into sys._MEIPASS.
    bundle_dir = getattr(sys, "_MEIPASS", None)
    if bundle_dir:
        return Path(bundle_dir) / "resources"
    return Path(__file__).resolve().parents[2] / "resources"


def _load_stylesheet(app: QApplication, theme: str = "dark") -> None:
    qss_path = _resource_path() / "styles" / f"{theme}.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)

    ctx = AppContext.create()
    _load_stylesheet(app, ctx.config_manager.config.theme.value)

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow(ctx)
    window.show()

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
