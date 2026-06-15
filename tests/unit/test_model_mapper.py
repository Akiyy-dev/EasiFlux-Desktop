"""Unit tests for model mapper."""

from decimal import Decimal

from easiflux_desktop.adapters.model_mapper import ModelMapper


def test_to_desktop_ticker():
    raw = {
        "symbol": "BTCUSDT",
        "last_price": "50000",
        "bid_price": "49999",
        "ask_price": "50001",
        "volume_24h": "1234.5",
    }
    ticker = ModelMapper.to_desktop_ticker(raw)
    assert ticker.symbol == "BTCUSDT"
    assert ticker.last_price == Decimal("50000")
    assert ticker.spread == Decimal("2")


def test_kline_from_raw():
    raw = {"open": "100", "high": "110", "low": "90", "close": "105", "volume": "50", "timestamp": 1700000000000}
    kline = ModelMapper.kline_from_raw(raw, "BTCUSDT", "1")
    assert kline.symbol == "BTCUSDT"
    assert kline.close == Decimal("105")


def test_to_desktop_order():
    raw = {
        "order_id": "123",
        "symbol": "BTCUSDT",
        "side": "Buy",
        "order_type": "Limit",
        "price": "50000",
        "qty": "0.01",
        "status": "New",
    }
    order = ModelMapper.to_desktop_order(raw)
    assert order.order_id == "123"
    assert order.status_display == "新建"


def test_to_sdk_order_request():
    from easiflux_sdk import OrderSide, OrderType

    from easiflux_desktop.models.trading import PlaceOrderRequest

    req = PlaceOrderRequest(symbol="BTCUSDT", side="Buy", order_type="Limit", qty="0.01", price="50000")
    sdk_req = ModelMapper.to_sdk_order_request(req)
    assert sdk_req.side == OrderSide.BUY
    assert sdk_req.order_type == OrderType.LIMIT
