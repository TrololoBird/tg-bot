from __future__ import annotations

import asyncio
import logging
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


    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        return symbol.strip().upper().split(":", 1)[0]

    async def _deliver(self, signal: SignalEvent, active_settings) -> None:
        signal_symbol = self._normalize_symbol(signal.symbol.raw_symbol)
        for settings in active_settings:
            if signal.scanner_id not in settings.enabled_scanners:
                continue
            if signal.symbol.exchange not in settings.enabled_exchanges:
                continue
            normalized_blacklist = {self._normalize_symbol(item) for item in settings.blacklist_symbols}
            if signal_symbol in normalized_blacklist:
                continue
            if signal.score < settings.min_score_threshold:
                continue
            await self.dispatcher.send_signal(settings.chat_id, signal)

    async def run_once(self) -> None:
        active_settings = self.database.get_active_user_settings()
        for signal in await self._collect_signals():
            if self.database.is_duplicate(signal):
                continue
            await self._deliver(signal, active_settings)
            self.database.remember_signal(signal)

    async def run(self) -> None:
        try:
            while True:
                await self.run_once()
                await asyncio.sleep(self.interval_seconds)
        except asyncio.CancelledError:
            self.logger.info("orchestrator stopped")
            raise
