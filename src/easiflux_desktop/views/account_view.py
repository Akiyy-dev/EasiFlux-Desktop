"""Account balance and position view."""

from __future__ import annotations

import asyncio

from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from easiflux_desktop.core.commands import RefreshAccountCommand
from easiflux_desktop.core.context import AppContext
from easiflux_desktop.core.state_store import AccountState
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

        ctx.event_bus.subscribe("state.account.updated", self._on_account_state)
        self._render_account_state(ctx.state_store.account)

    async def _refresh(self) -> None:
        await self._ctx.command_bus.execute(RefreshAccountCommand(self._ctx.market_manager.active_symbol))

    def _on_account_state(self, state: AccountState) -> None:
        self._render_account_state(state)

    def _render_account_state(self, state: AccountState) -> None:
        self._equity_label.setText(f"总权益: {state.total_equity}")
        balances = state.balance_list()
        if balances:
            parts = [balance.available_display for balance in balances]
            self._balance_label.setText("余额: " + " | ".join(parts))
        else:
            self._balance_label.setText("余额: —")
