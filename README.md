"""Entry point for the unified crypto signal bot.

This module constructs the adapters, scanners and orchestrator and
starts the asynchronous event loop. It should be executed as a
module, e.g. ``python -m combined_bot.main``. The bot currently
relies on stubbed adapters and therefore does not produce real
signals; it is intended as a template to build upon.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Dict

from . import config
from .adapters import BinanceFuturesAdapter
from .delivery import TelegramDispatcher
from .core.orchestrator import Orchestrator
from .scanners import (
    VolumeSpikeScanner,
    PricePumpScanner,
    OpenInterestScanner,
    MachineLearningScanner,
)


def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL, logging.INFO),
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    )


async def main_async() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting unified crypto bot")
    # Construct adapters
    adapters: Dict[str, BinanceFuturesAdapter] = {}
    if "binance" in config.ENABLED_EXCHANGES.split(","):
        adapters["binance"] = BinanceFuturesAdapter()
    # Construct scanners
    scanners = [
        VolumeSpikeScanner(),
        PricePumpScanner(),
        OpenInterestScanner(),
        MachineLearningScanner(model_path=None),
    ]
    dispatcher = TelegramDispatcher()
    orchestrator = Orchestrator(
        adapters=adapters,
        scanners=scanners,
        dispatcher=dispatcher,
        scan_interval=config.DEFAULT_SCAN_INTERVAL_SECONDS,
        heartbeat_interval=config.HEARTBEAT_INTERVAL,
    )
    try:
        await orchestrator.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt; stopping orchestrator...")
        await orchestrator.stop()


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()