from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

import ccxt.async_support as ccxt

from .. import config
from .base import BaseExchangeAdapter


class BinanceFuturesAdapter(BaseExchangeAdapter):
    exchange_id = "binance"

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self._client = ccxt.binanceusdm(
            {
                "enableRateLimit": True,
                "timeout": config.ADAPTER_TIMEOUT_MS,
            }
        )
        self._markets_loaded = False
        self._symbols_cache: List[str] = []
        self._symbols_cached_at = 0.0

    async def _with_retry(self, operation_name: str, operation):
        attempts = max(1, config.ADAPTER_RETRY_ATTEMPTS)
        base_delay = max(0.1, config.ADAPTER_RETRY_BASE_DELAY_SECONDS)
        for attempt in range(1, attempts + 1):
            try:
                return await operation()
            except (ccxt.NetworkError, ccxt.RequestTimeout, ccxt.ExchangeNotAvailable, ccxt.DDoSProtection, ccxt.RateLimitExceeded) as exc:
                is_last = attempt == attempts
                self.logger.warning(
                    "adapter operation failed (%s) attempt %s/%s: %s",
                    operation_name,
                    attempt,
                    attempts,
                    exc,
                )
                if is_last:
                    raise
                await asyncio.sleep(base_delay * (2 ** (attempt - 1)))

    async def _ensure_markets_loaded(self) -> None:
        if not self._markets_loaded:
            await self._with_retry("load_markets", self._client.load_markets)
            self._markets_loaded = True

    async def list_symbols(self) -> List[str]:
        await self._ensure_markets_loaded()
        now = time.monotonic()
        if self._symbols_cache and now - self._symbols_cached_at < config.SYMBOLS_CACHE_TTL_SECONDS:
            return list(self._symbols_cache)

        symbols: List[str] = []
        for market in self._client.markets.values():
            if market.get("active") and market.get("swap") and market.get("linear") and market.get("quote") == "USDT":
                symbols.append(str(market["symbol"]))

        symbols.sort(key=lambda item: str(item))
        if config.TOP_SYMBOLS_LIMIT > 0:
            symbols = symbols[: config.TOP_SYMBOLS_LIMIT]

        self._symbols_cache = list(symbols)
        self._symbols_cached_at = now
        return symbols

    async def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int) -> List[List[Any]]:
        await self._ensure_markets_loaded()

        async def _op():
            return await self._client.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

        return await self._with_retry(f"fetch_ohlcv:{symbol}:{timeframe}", _op)

    async def fetch_open_interest_history(self, symbol: str, days: int) -> List[Dict[str, Any]]:
        await self._ensure_markets_loaded()

        async def _op():
            return await self._client.fetch_open_interest_history(symbol, timeframe="1d", limit=days)

        history = await self._with_retry(f"fetch_open_interest_history:{symbol}", _op)
        return [{"ts": item.get("timestamp", 0), "oi": item.get("openInterestAmount", 0)} for item in history]

    async def close(self) -> None:
        await self._client.close()
