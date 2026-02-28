from __future__ import annotations

import asyncio
import logging

from combined_bot import config
from combined_bot.adapters.binance import BinanceFuturesAdapter
from combined_bot.core.database import Database
from combined_bot.core.orchestrator import Orchestrator
from combined_bot.delivery.telegram_dispatcher import TelegramDispatcher
from combined_bot.scanners import MachineLearningScanner, OpenInterestScanner, PricePumpScanner, VolumeSpikeScanner


def build_orchestrator() -> Orchestrator:
    logging.basicConfig(level=config.LOG_LEVEL)
    database = Database(config.DATABASE_PATH)
    adapters = {"binance": BinanceFuturesAdapter()}
    scanners = [
        VolumeSpikeScanner(),
        PricePumpScanner(),
        OpenInterestScanner(),
        MachineLearningScanner(),
    ]
    dispatcher = TelegramDispatcher()
    return Orchestrator(adapters=adapters, scanners=scanners, database=database, dispatcher=dispatcher)


if __name__ == "__main__":
    orchestrator = build_orchestrator()
    asyncio.run(orchestrator.run())
