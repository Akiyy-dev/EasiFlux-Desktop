"""Market data subscription and caching."""

from __future__ import annotations

import asyncio
import logging

from easiflux_desktop.adapters.rest_adapter import RestAdapter
from easiflux_desktop.adapters.ws_adapter import WsAdapter
from easiflux_desktop.core.constants import TICKER_POLL_INTERVAL_SEC
from easiflux_desktop.core.errors import ValidationError
from easiflux_desktop.core.event_bus import EventBus
from easiflux_desktop.models.market import DesktopDepth, DesktopKline, DesktopTicker
from easiflux_desktop.services.config_manager import ConfigManager
from easiflux_desktop.storage.cache_store import CacheStore

logger = logging.getLogger(__name__)


class MarketManager:
    def __init__(
        self,
        rest: RestAdapter,
        ws: WsAdapter,
        cache: CacheStore,
        config_manager: ConfigManager,
        event_bus: EventBus,
    ) -> None:
        self._rest = rest
        self._ws = ws
        self._cache = cache
        self._config_manager = config_manager
        self._event_bus = event_bus
        self._active_symbol = config_manager.config.active_symbol
        self._poll_task: asyncio.Task[None] | None = None

    @property
    def active_symbol(self) -> str:
        return self._active_symbol

    @property
    def watchlist_symbols(self) -> list[str]:
        symbols = [self._normalize_symbol(symbol) for symbol in self._config_manager.config.watchlist_symbols]
        if self._active_symbol not in symbols:
            symbols.insert(0, self._active_symbol)
        return symbols

    def set_active_symbol(self, symbol: str, *, persist: bool = True) -> str:
        normalized = self._normalize_symbol(symbol)
        self._active_symbol = normalized
        if persist:
            config = self._config_manager.config
            config.active_symbol = normalized
            if normalized not in config.watchlist_symbols:
                config.watchlist_symbols.insert(0, normalized)
                config.watchlist_symbols = config.watchlist_symbols[:20]
            self._config_manager.save_config()
        self._event_bus.publish("market.active_symbol_changed", normalized)
        return normalized

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        normalized = symbol.strip().upper()
        if not normalized:
            raise ValidationError("交易对不能为空")
        return normalized

    async def fetch_ticker(self, symbol: str | None = None) -> DesktopTicker:
        sym = symbol or self._active_symbol
        ticker = await self._rest.get_ticker(sym)
        self._cache.set_ticker(ticker)
        self._event_bus.publish("ticker.updated", ticker)
        return ticker

    async def get_klines(
        self,
        symbol: str | None = None,
        interval: str | None = None,
        *,
        limit: int = 200,
    ) -> list[DesktopKline]:
        sym = symbol or self._active_symbol
        iv = interval or self._config_manager.config.kline_interval
        klines = await self._rest.get_klines(sym, iv, limit=limit)
        self._cache.set_klines(sym, iv, klines)
        self._event_bus.publish("klines.loaded", {"symbol": sym, "interval": iv, "klines": klines})
        for kline in klines[-10:]:
            self._event_bus.publish("kline.updated", kline)
        return klines

    async def get_depth(self, symbol: str | None = None, *, limit: int = 20) -> DesktopDepth:
        sym = symbol or self._active_symbol
        depth = await self._rest.get_depth(sym, limit=limit)
        self._event_bus.publish("depth.updated", depth)
        return depth

    async def refresh_snapshot(self, symbol: str | None = None) -> dict[str, object]:
        sym = self._normalize_symbol(symbol or self._active_symbol)
        ticker = await self.fetch_ticker(sym)
        depth = await self.get_depth(sym)
        klines = await self.get_klines(sym)
        return {"symbol": sym, "ticker": ticker, "depth": depth, "klines": klines}

    async def subscribe_ticker(self, symbol: str | None = None) -> None:
        sym = symbol or self._active_symbol
        config = self._config_manager.config

        if config.use_websocket:
            await self._ws.subscribe_ticker(sym)
            await self._ws.subscribe_depth(sym)
        else:
            await self.start_polling(sym)

    async def start_polling(self, symbol: str | None = None) -> None:
        await self.stop_polling()
        sym = symbol or self._active_symbol
        interval = self._config_manager.config.ticker_poll_interval or TICKER_POLL_INTERVAL_SEC

        async def _poll() -> None:
            while True:
                try:
                    await self.fetch_ticker(sym)
                except Exception as exc:
                    logger.warning("Ticker poll failed: %s", exc)
                await asyncio.sleep(interval)

        self._poll_task = asyncio.create_task(_poll())

    async def stop_polling(self) -> None:
        if self._poll_task is not None:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
            self._poll_task = None

    async def start_realtime(self, symbol: str | None = None) -> None:
        sym = symbol or self._active_symbol
        config = self._config_manager.config
        if config.use_websocket:
            await self._ws.subscribe_all(sym)
        else:
            await self.start_polling(sym)

    async def stop_realtime(self) -> None:
        await self.stop_polling()
        await self._ws.stop()
