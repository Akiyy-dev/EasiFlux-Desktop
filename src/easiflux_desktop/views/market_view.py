"""Market data view combining ticker, kline and depth."""

from __future__ import annotations

import asyncio

from PySide6.QtCore import QSignalBlocker
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QSplitter, QVBoxLayout, QWidget

from easiflux_desktop.core.commands import RefreshMarketCommand, SetActiveSymbolCommand
from easiflux_desktop.core.context import AppContext
from easiflux_desktop.core.state_store import MarketState
from easiflux_desktop.widgets.kline_chart import KlineChart
from easiflux_desktop.widgets.order_book import OrderBookWidget
from easiflux_desktop.widgets.ticker_bar import TickerBar


class MarketView(QWidget):
    def __init__(self, ctx: AppContext, parent=None) -> None:
        super().__init__(parent)
        self._ctx = ctx
        self._rendered_symbol: str | None = None
        layout = QVBoxLayout(self)
        layout.addLayout(self._build_symbol_toolbar())
        layout.addWidget(TickerBar(ctx))

        splitter = QSplitter()
        splitter.addWidget(KlineChart(ctx))
        splitter.addWidget(OrderBookWidget(ctx))
        splitter.setSizes([700, 300])
        layout.addWidget(splitter)

        ctx.event_bus.subscribe("state.market.updated", self._on_market_state)

    def _build_symbol_toolbar(self) -> QHBoxLayout:
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("交易对"))
        self._symbol_combo = QComboBox()
        self._symbol_combo.setEditable(True)
        self._sync_symbol_choices(self._ctx.market_manager.active_symbol)
        toolbar.addWidget(self._symbol_combo)

        self._switch_btn = QPushButton("切换")
        self._switch_btn.clicked.connect(lambda: asyncio.create_task(self._switch_symbol()))
        toolbar.addWidget(self._switch_btn)

        self._refresh_btn = QPushButton("刷新行情")
        self._refresh_btn.clicked.connect(lambda: asyncio.create_task(self._refresh_market()))
        toolbar.addWidget(self._refresh_btn)

        self._status = QLabel(f"当前交易对: {self._ctx.market_manager.active_symbol}")
        toolbar.addWidget(self._status)
        toolbar.addStretch()
        return toolbar

    def _sync_symbol_choices(self, active_symbol: str) -> None:
        blocker = QSignalBlocker(self._symbol_combo)
        symbols = list(self._ctx.market_manager.watchlist_symbols)
        if active_symbol not in symbols:
            symbols.insert(0, active_symbol)
        self._symbol_combo.clear()
        self._symbol_combo.addItems(symbols)
        self._symbol_combo.setCurrentText(active_symbol)
        self._rendered_symbol = active_symbol
        del blocker

    def _current_symbol(self) -> str:
        return self._symbol_combo.currentText().strip().upper()

    async def _switch_symbol(self) -> None:
        symbol = self._current_symbol()
        if not symbol:
            self._status.setText("交易对不能为空")
            return
        self._set_busy(True, f"正在切换到 {symbol}...")
        try:
            result = await self._ctx.command_bus.execute(SetActiveSymbolCommand(symbol))
            if result.success:
                self._sync_symbol_choices(result.data)
                self._status.setText(f"当前交易对: {result.data}")
            elif result.error:
                self._status.setText(f"切换失败: {result.error.user_message}")
        finally:
            self._set_busy(False)

    async def _refresh_market(self) -> None:
        symbol = self._current_symbol()
        if not symbol:
            self._status.setText("交易对不能为空")
            return
        self._set_busy(True, f"正在刷新 {symbol}...")
        try:
            result = await self._ctx.command_bus.execute(RefreshMarketCommand(symbol))
            if result.success:
                self._status.setText(f"行情已刷新: {symbol}")
            elif result.error:
                self._status.setText(f"行情刷新失败: {result.error.user_message}")
        finally:
            self._set_busy(False)

    def _set_busy(self, busy: bool, status: str | None = None) -> None:
        self._switch_btn.setEnabled(not busy)
        self._refresh_btn.setEnabled(not busy)
        if status:
            self._status.setText(status)

    def _on_market_state(self, state: MarketState) -> None:
        if state.active_symbol != self._rendered_symbol:
            self._sync_symbol_choices(state.active_symbol)
            self._status.setText(f"当前交易对: {state.active_symbol}")
