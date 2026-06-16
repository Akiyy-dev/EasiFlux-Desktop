"""Order book depth display widget."""

from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGroupBox, QTableWidget, QTableWidgetItem, QVBoxLayout

from easiflux_desktop.core.context import AppContext
from easiflux_desktop.core.state_store import MarketState
from easiflux_desktop.models.market import DesktopDepth


class OrderBookWidget(QGroupBox):
    def __init__(self, ctx: AppContext, parent=None) -> None:
        super().__init__("深度", parent)
        self._ctx = ctx
        layout = QVBoxLayout(self)
        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["买价", "买量", "卖价", "卖量"])
        self._table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self._table)
        ctx.event_bus.subscribe("state.market.updated", self._on_market_state)
        depth = ctx.state_store.market.depth()
        if depth is not None:
            self.set_depth(depth)

    def set_depth(self, depth: DesktopDepth) -> None:
        rows = max(len(depth.bids), len(depth.asks), 1)
        self._table.setRowCount(rows)
        for i in range(rows):
            if i < len(depth.bids):
                bid = depth.bids[i]
                bid_price = QTableWidgetItem(str(bid.price))
                bid_price.setForeground(QColor("#26a69a"))
                bid_size = QTableWidgetItem(str(bid.size))
                self._table.setItem(i, 0, bid_price)
                self._table.setItem(i, 1, bid_size)
            if i < len(depth.asks):
                ask = depth.asks[i]
                ask_price = QTableWidgetItem(str(ask.price))
                ask_price.setForeground(QColor("#ef5350"))
                ask_size = QTableWidgetItem(str(ask.size))
                self._table.setItem(i, 2, ask_price)
                self._table.setItem(i, 3, ask_size)

    def _on_market_state(self, state: MarketState) -> None:
        depth = state.depth()
        if depth is not None:
            self.set_depth(depth)
