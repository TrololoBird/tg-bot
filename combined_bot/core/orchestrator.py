from __future__ import annotations

import asyncio
import logging
import time
from typing import Dict, List

from .. import config
from ..adapters.base import BaseExchangeAdapter
from ..core.database import Database
from ..delivery.telegram_dispatcher import TelegramDispatcher
from ..models import SignalEvent
from ..scanners.base import BaseScanner


class Orchestrator:
    def __init__(
        self,
        adapters: Dict[str, BaseExchangeAdapter],
        scanners: List[BaseScanner],
        database: Database,
        dispatcher: TelegramDispatcher,
        interval_seconds: int = config.SCAN_INTERVAL_SECONDS,
    ) -> None:
        self.adapters = adapters
        self.scanners = scanners
        self.database = database
        self.dispatcher = dispatcher
        self.interval_seconds = interval_seconds
        self.logger = logging.getLogger(self.__class__.__name__)

    async def _collect_signals(self) -> List[SignalEvent]:
        tasks = [scanner.scan(self.adapters) for scanner in self.scanners]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        signals: List[SignalEvent] = []
        for result in results:
            if isinstance(result, Exception):
                self.logger.exception("scanner failed", exc_info=result)
                continue
            signals.extend(result)
        return signals

    async def _deliver(self, signal: SignalEvent, active_settings) -> int:
        delivered = 0
        signal_symbol = signal.symbol.canonical_symbol
        for settings in active_settings:
            if signal.scanner_id not in settings.enabled_scanners:
                continue
            if signal.symbol.exchange not in settings.enabled_exchanges:
                continue
            if signal_symbol in settings.blacklist_symbols:
                continue
            if signal.score < settings.min_score_threshold:
                continue
            await self.dispatcher.send_signal(settings.chat_id, signal)
            delivered += 1
        return delivered

    async def run_once(self) -> None:
        # The current delivery flow is designed for a single process/worker.
        # Do not run multiple bot instances against the same database unless delivery reservation becomes atomic.
        cycle_started = time.monotonic()
        active_settings = self.database.get_active_user_settings()
        signals = await self._collect_signals()
        duplicates = 0
        delivered = 0
        for signal in signals:
            if self.database.is_duplicate(signal):
                duplicates += 1
                continue
            delivered += await self._deliver(signal, active_settings)
            self.database.remember_signal(signal)
        elapsed = time.monotonic() - cycle_started
        self.logger.info(
            "cycle finished users=%s signals=%s delivered=%s duplicates=%s duration_sec=%.2f",
            len(active_settings),
            len(signals),
            delivered,
            duplicates,
            elapsed,
        )

    async def run(self) -> None:
        try:
            while True:
                await self.run_once()
                await asyncio.sleep(self.interval_seconds)
        except asyncio.CancelledError:
            self.logger.info("orchestrator stopped")
            raise
        finally:
            for adapter in self.adapters.values():
                try:
                    await adapter.close()
                except Exception:
                    self.logger.exception("failed to close adapter")
            try:
                await self.dispatcher.close()
            except Exception:
                self.logger.exception("failed to close dispatcher")
