"""SDK ↔ Desktop model conversion utilities."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from easiflux_sdk.models import Balance, Order, OrderRequest, OrderSide, OrderType, Position, Ticker

from easiflux_desktop.models.account import DesktopBalance
from easiflux_desktop.models.market import DepthLevel, DesktopDepth, DesktopKline, DesktopTicker
from easiflux_desktop.models.trading import DesktopOrder, DesktopPosition, OrderStatus, PlaceOrderRequest, PositionSide


def _decimal(value: object | None) -> Decimal:
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


def extract_data(payload: Any) -> Any:
    """Unwrap common API response envelopes."""
    if not isinstance(payload, dict):
        return payload
    if "data" in payload:
        return payload["data"]
    return payload


def extract_list(payload: Any) -> list[dict[str, Any]]:
    data = extract_data(payload)
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in ("list", "items", "records", "orders", "positions", "balances", "tickers"):
            items = data.get(key)
            if isinstance(items, list):
                return [item for item in items if isinstance(item, dict)]
        return [data]
    return []


class ModelMapper:
    @staticmethod
    def to_desktop_ticker(data: dict[str, Any] | Ticker, symbol: str | None = None) -> DesktopTicker:
        if isinstance(data, Ticker):
            raw = {
                "symbol": data.symbol,
                "last_price": data.last_price,
                "bid_price": data.bid_price,
                "ask_price": data.ask_price,
                "volume_24h": data.volume_24h,
            }
        else:
            raw = data

        sym = str(raw.get("symbol") or symbol or "")
        return DesktopTicker(
            symbol=sym,
            last_price=_decimal(raw.get("last_price") or raw.get("lastPrice") or raw.get("price")),
            bid_price=_decimal(raw.get("bid_price") or raw.get("bidPrice") or raw.get("bid1Price")),
            ask_price=_decimal(raw.get("ask_price") or raw.get("askPrice") or raw.get("ask1Price")),
            volume_24h=_decimal(raw.get("volume_24h") or raw.get("volume24h") or raw.get("volume")),
            change_24h=_decimal(raw.get("change_24h") or raw.get("price24hPcnt")),
            change_pct=_decimal(raw.get("change_pct") or raw.get("price24hPcnt")),
        )

    @staticmethod
    def kline_from_raw(raw: dict[str, Any], symbol: str, interval: str) -> DesktopKline:
        ts_raw = raw.get("timestamp") or raw.get("start") or raw.get("openTime") or raw.get("time") or 0
        ts_ms = int(ts_raw)
        if ts_ms < 10_000_000_000:
            ts_ms *= 1000
        return DesktopKline(
            symbol=symbol,
            interval=interval,
            open=_decimal(raw.get("open") or raw.get("o")),
            high=_decimal(raw.get("high") or raw.get("h")),
            low=_decimal(raw.get("low") or raw.get("l")),
            close=_decimal(raw.get("close") or raw.get("c")),
            volume=_decimal(raw.get("volume") or raw.get("v")),
            timestamp=datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc),
        )

    @staticmethod
    def klines_from_payload(payload: Any, symbol: str, interval: str) -> list[DesktopKline]:
        items = extract_list(payload)
        return [ModelMapper.kline_from_raw(item, symbol, interval) for item in items]

    @staticmethod
    def depth_from_payload(payload: Any, symbol: str) -> DesktopDepth:
        data = extract_data(payload)
        if not isinstance(data, dict):
            data = {}

        bids_raw = data.get("bids") or data.get("b") or []
        asks_raw = data.get("asks") or data.get("a") or []

        def _levels(levels: list) -> list[DepthLevel]:
            result: list[DepthLevel] = []
            for level in levels:
                if isinstance(level, (list, tuple)) and len(level) >= 2:
                    result.append(DepthLevel(price=_decimal(level[0]), size=_decimal(level[1])))
                elif isinstance(level, dict):
                    result.append(
                        DepthLevel(
                            price=_decimal(level.get("price") or level.get("p")),
                            size=_decimal(level.get("size") or level.get("qty") or level.get("q")),
                        )
                    )
            return result

        return DesktopDepth(symbol=symbol, bids=_levels(bids_raw), asks=_levels(asks_raw))

    @staticmethod
    def to_desktop_order(data: dict[str, Any] | Order) -> DesktopOrder:
        if isinstance(data, Order):
            raw: dict[str, Any] = {
                "order_id": data.order_id,
                "order_link_id": data.order_link_id,
                "symbol": data.symbol,
                "side": data.side,
                "order_type": data.order_type,
                "price": data.price,
                "qty": data.qty,
                "status": data.status,
            }
        else:
            raw = data

        return DesktopOrder(
            order_id=str(raw.get("order_id") or raw.get("orderId") or ""),
            order_link_id=raw.get("order_link_id") or raw.get("orderLinkId"),
            symbol=str(raw.get("symbol") or ""),
            side=str(raw.get("side") or ""),
            order_type=str(raw.get("order_type") or raw.get("orderType") or ""),
            price=_decimal(raw.get("price")),
            qty=_decimal(raw.get("qty") or raw.get("quantity")),
            status=OrderStatus.from_raw(str(raw.get("status") or "")),
            filled_qty=_decimal(raw.get("filled_qty") or raw.get("cumExecQty")),
            avg_price=_decimal(raw.get("avg_price") or raw.get("avgPrice")),
        )

    @staticmethod
    def orders_from_payload(payload: Any) -> list[DesktopOrder]:
        return [ModelMapper.to_desktop_order(item) for item in extract_list(payload)]

    @staticmethod
    def to_desktop_position(data: dict[str, Any] | Position) -> DesktopPosition:
        if isinstance(data, Position):
            raw: dict[str, Any] = {
                "symbol": data.symbol,
                "side": data.side,
                "size": data.size,
                "entry_price": data.entry_price,
                "leverage": data.leverage,
                "unrealised_pnl": data.unrealised_pnl,
            }
        else:
            raw = data

        return DesktopPosition(
            symbol=str(raw.get("symbol") or ""),
            side=PositionSide.from_raw(str(raw.get("side") or "")),
            size=_decimal(raw.get("size") or raw.get("qty")),
            entry_price=_decimal(raw.get("entry_price") or raw.get("avgPrice") or raw.get("entryPrice")),
            leverage=_decimal(raw.get("leverage")),
            unrealised_pnl=_decimal(raw.get("unrealised_pnl") or raw.get("unrealisedPnl") or raw.get("pnl")),
        )

    @staticmethod
    def positions_from_payload(payload: Any) -> list[DesktopPosition]:
        return [ModelMapper.to_desktop_position(item) for item in extract_list(payload)]

    @staticmethod
    def to_desktop_balance(data: dict[str, Any] | Balance) -> DesktopBalance:
        if isinstance(data, Balance):
            raw: dict[str, Any] = {
                "coin": data.coin,
                "equity": data.equity,
                "wallet_balance": data.wallet_balance,
                "available_balance": data.available_balance,
            }
        else:
            raw = data

        return DesktopBalance(
            coin=str(raw.get("coin") or raw.get("currency") or "USDT"),
            equity=_decimal(raw.get("equity") or raw.get("totalEquity")),
            wallet_balance=_decimal(raw.get("wallet_balance") or raw.get("walletBalance")),
            available_balance=_decimal(raw.get("available_balance") or raw.get("availableBalance")),
        )

    @staticmethod
    def balances_from_payload(payload: Any) -> list[DesktopBalance]:
        return [ModelMapper.to_desktop_balance(item) for item in extract_list(payload)]

    @staticmethod
    def to_sdk_order_request(request: PlaceOrderRequest) -> OrderRequest:
        side = OrderSide.BUY if request.side.lower() in ("buy", "long") else OrderSide.SELL
        order_type = OrderType.MARKET if request.order_type.lower() == "market" else OrderType.LIMIT
        return OrderRequest(
            symbol=request.symbol,
            side=side,
            order_type=order_type,
            qty=request.qty,
            price=request.price,
        )
