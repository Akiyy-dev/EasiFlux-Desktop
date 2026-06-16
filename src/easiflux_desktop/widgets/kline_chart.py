"""K-line chart widget using PyQtGraph."""

from __future__ import annotations

import pyqtgraph as pg
from PySide6.QtWidgets import QComboBox, QGroupBox, QHBoxLayout, QVBoxLayout

from easiflux_desktop.core.commands import LoadKlinesCommand
from easiflux_desktop.core.constants import KLINE_INTERVALS
from easiflux_desktop.core.context import AppContext
from easiflux_desktop.core.state_store import MarketState
from easiflux_desktop.models.market import DesktopKline


class KlineChart(QGroupBox):
    def __init__(self, ctx: AppContext, parent=None) -> None:
        super().__init__("K线图", parent)
        self._ctx = ctx
        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        self._interval = QComboBox()
        self._interval.addItems(list(KLINE_INTERVALS))
        self._interval.setCurrentText(ctx.config_manager.config.kline_interval)
        self._interval.currentTextChanged.connect(self._on_interval_changed)
        toolbar.addWidget(self._interval)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        pg.setConfigOptions(antialias=True)
        self._plot = pg.PlotWidget()
        self._plot.setBackground("#1e1e1e")
        self._plot.showGrid(x=True, y=True, alpha=0.3)
        self._plot.setLabel("left", "价格")
        self._plot.setLabel("bottom", "时间")
        self._candle = pg.PlotDataItem()
        self._plot.addItem(self._candle)
        layout.addWidget(self._plot)

        ctx.event_bus.subscribe("state.klines.updated", self._on_klines_state)
        self.set_klines(ctx.state_store.market.kline_series(interval=ctx.config_manager.config.kline_interval))

    def _on_interval_changed(self, interval: str) -> None:
        config = self._ctx.config_manager.config
        config.kline_interval = interval
        self._ctx.config_manager.save_config()
        import asyncio
        asyncio.create_task(self._ctx.command_bus.execute(LoadKlinesCommand(interval=interval)))

    def set_klines(self, klines: list[DesktopKline]) -> None:
        if not klines:
            return
        closes = [float(k.close) for k in klines]
        xs = list(range(len(closes)))
        self._candle.setData(xs, closes, pen=pg.mkPen("#26a69a", width=2))

    def _on_klines_state(self, state: MarketState) -> None:
        symbol = self._ctx.market_manager.active_symbol
        interval = self._ctx.config_manager.config.kline_interval
        klines = state.kline_series(symbol, interval)
        self.set_klines(klines)
