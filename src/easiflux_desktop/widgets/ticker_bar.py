"""Ticker display bar widget."""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from easiflux_desktop.core.context import AppContext
from easiflux_desktop.models.market import DesktopTicker


class TickerBar(QWidget):
    def __init__(self, ctx: AppContext, parent=None) -> None:
        super().__init__(parent)
        self._ctx = ctx
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        self._symbol = QLabel("—")
        self._symbol.setStyleSheet("font-size: 16px; font-weight: bold;")
        self._last = QLabel("—")
        self._bid = QLabel("买: —")
        self._ask = QLabel("卖: —")
        self._spread = QLabel("价差: —")
        self._volume = QLabel("24h量: —")

        for widget in (self._symbol, self._last, self._bid, self._ask, self._spread, self._volume):
            layout.addWidget(widget)
        layout.addStretch()

        ctx.event_bus.subscribe("ticker.updated", self._on_ticker)

    def _on_ticker(self, ticker: DesktopTicker) -> None:
        self._symbol.setText(ticker.symbol)
        self._last.setText(f"最新: {ticker.last_price}")
        self._bid.setText(f"买: {ticker.bid_price}")
        self._ask.setText(f"卖: {ticker.ask_price}")
        self._spread.setText(f"价差: {ticker.spread}")
        self._volume.setText(f"24h量: {ticker.volume_display}")
