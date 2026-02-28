from __future__ import annotations

from ..models import SignalEvent


class TelegramDispatcher:
    async def send_signal(self, chat_id: int, signal: SignalEvent) -> None:
        _ = chat_id, signal
        # Stub: integrate aiogram/python-telegram-bot here.
        return
