"""Persistent local trade log storage."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

from platformdirs import user_data_dir

from easiflux_desktop.core.constants import APP_NAME, APP_ORG
from easiflux_desktop.models.trading import DesktopOrder


class TradeLogStore:
    ORDER_HEADERS = [
        "logged_at",
        "order_id",
        "symbol",
        "side",
        "type",
        "price",
        "qty",
        "status",
        "filled_qty",
        "avg_price",
    ]

    def __init__(self, directory: Path | None = None) -> None:
        self._directory = directory or Path(user_data_dir(APP_NAME, APP_ORG))
        self._directory.mkdir(parents=True, exist_ok=True)
        self._orders_path = self._directory / "orders.csv"
        self._exports_dir = self._directory / "exports"
        self._exports_dir.mkdir(parents=True, exist_ok=True)

    @property
    def orders_path(self) -> Path:
        return self._orders_path

    @property
    def exports_dir(self) -> Path:
        return self._exports_dir

    def record_order(self, order: DesktopOrder) -> None:
        write_header = not self._orders_path.exists()
        with self._orders_path.open("a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=self.ORDER_HEADERS)
            if write_header:
                writer.writeheader()
            writer.writerow(
                {
                    "logged_at": datetime.now(timezone.utc).isoformat(),
                    "order_id": order.order_id,
                    "symbol": order.symbol,
                    "side": order.side,
                    "type": order.order_type,
                    "price": str(order.price),
                    "qty": str(order.qty),
                    "status": order.status.value,
                    "filled_qty": str(order.filled_qty),
                    "avg_price": str(order.avg_price),
                }
            )

    def export_text(self, filename: str, content: str) -> Path:
        safe_name = filename.replace("/", "_").replace("\\", "_")
        path = self._exports_dir / safe_name
        path.write_text(content, encoding="utf-8")
        return path
