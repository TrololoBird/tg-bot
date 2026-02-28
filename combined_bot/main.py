from __future__ import annotations

import asyncio
import logging

from combined_bot import config
from combined_bot.adapters.binance import BinanceFuturesAdapter
from combined_bot.core.database import Database
from combined_bot.core.orchestrator import Orchestrator
from combined_bot.delivery.telegram_dispatcher import TelegramDispatcher
from combined_bot.scanners import OpenInterestScanner, PricePumpScanner, VolumeSpikeScanner


def _build_adapters() -> dict[str, BinanceFuturesAdapter]:
    available_adapters = {
        "binance": BinanceFuturesAdapter,
    }
    adapters: dict[str, BinanceFuturesAdapter] = {}
    for exchange in config.ENABLED_EXCHANGES:
        exchange_id = exchange.strip().lower()
        adapter_class = available_adapters.get(exchange_id)
        if adapter_class is None:
            logging.getLogger(__name__).warning("exchange is not supported: %s", exchange)
            continue
        adapters[exchange_id] = adapter_class()
    if not adapters:
        adapters["binance"] = BinanceFuturesAdapter()
        logging.getLogger(__name__).warning("no supported exchanges configured, falling back to binance")
    return adapters


def build_orchestrator() -> Orchestrator:
    logging.basicConfig(level=getattr(logging, config.LOG_LEVEL, logging.INFO))
    database = Database(config.DATABASE_PATH)
    adapters = _build_adapters()
    scanners = [
        VolumeSpikeScanner(),
        PricePumpScanner(),
        OpenInterestScanner(),
    ]
    dispatcher = TelegramDispatcher()
    return Orchestrator(adapters=adapters, scanners=scanners, database=database, dispatcher=dispatcher)


if __name__ == "__main__":
    orchestrator = build_orchestrator()
    asyncio.run(orchestrator.run())
