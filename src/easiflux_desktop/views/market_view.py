"""Market data view combining ticker, kline and depth."""

from __future__ import annotations

from PySide6.QtWidgets import QSplitter, QVBoxLayout, QWidget

from easiflux_desktop.core.context import AppContext
from easiflux_desktop.widgets.kline_chart import KlineChart
from easiflux_desktop.widgets.order_book import OrderBookWidget
from easiflux_desktop.widgets.ticker_bar import TickerBar


class MarketView(QWidget):
    def __init__(self, ctx: AppContext, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(TickerBar(ctx))

        splitter = QSplitter()
        splitter.addWidget(KlineChart(ctx))
        splitter.addWidget(OrderBookWidget(ctx))
        splitter.setSizes([700, 300])
        layout.addWidget(splitter)
