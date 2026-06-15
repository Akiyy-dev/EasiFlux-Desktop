"""Account balance and position view."""

from __future__ import annotations

import asyncio

from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from easiflux_desktop.core.context import AppContext
from easiflux_desktop.widgets.position_table import PositionTable


class AccountView(QGroupBox):
    def __init__(self, ctx: AppContext, parent=None) -> None:
        super().__init__("账户", parent)
        self._ctx = ctx
        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        self._equity_label = QLabel("总权益: —")
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(lambda: asyncio.create_task(self._refresh()))
        toolbar.addWidget(self._equity_label)
        toolbar.addStretch()
        toolbar.addWidget(refresh_btn)
        layout.addLayout(toolbar)

        self._balance_label = QLabel("余额: —")
        layout.addWidget(self._balance_label)

        self._position_table = PositionTable(ctx)
        layout.addWidget(self._position_table)

        ctx.event_bus.subscribe("balance.updated", self._on_balance)

    async def _refresh(self) -> None:
        account = await self._ctx.account_manager.refresh_account(
            self._ctx.market_manager.active_symbol
        )
        self._equity_label.setText(f"总权益: {account.total_equity_usd}")
        if account.balances:
            parts = [b.available_display for b in account.balances]
            self._balance_label.setText("余额: " + " | ".join(parts))
        positions = await self._ctx.account_manager.get_positions(
            self._ctx.market_manager.active_symbol
        )
        self._position_table.set_positions(positions)

    def _on_balance(self, balance) -> None:
        self._balance_label.setText(f"余额: {balance.available_display}")
