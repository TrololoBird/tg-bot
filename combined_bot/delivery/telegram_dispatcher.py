from __future__ import annotations

from datetime import timezone
from html import escape
from typing import Optional

from telegram import Bot

from .. import config
from ..models import SignalEvent


class TelegramDispatcher:
    def __init__(self, token: Optional[str] = None) -> None:
        self._token = (token if token is not None else config.TG_BOT_TOKEN).strip()
        self._bot: Optional[Bot] = Bot(token=self._token) if self._token else None

    @staticmethod
    def _binance_link(symbol: str) -> str:
        compact = symbol.replace("/", "").split(":", 1)[0].upper()
        return f"https://www.binance.com/en/futures/{compact}"

    @staticmethod
    def _format_metrics(signal: SignalEvent) -> str:
        metrics = signal.metrics
        scanner = signal.scanner_id
        if scanner == "vol_spike":
            return (
                f"• prev_24h_vol_usd: <b>{metrics.get('prev_24h_volume_usd', 0.0):,.0f}</b>\n"
                f"• last_24h_vol_usd: <b>{metrics.get('last_24h_volume_usd', 0.0):,.0f}</b>\n"
                f"• volume_ratio: <b>{metrics.get('ratio', 0.0):.2f}x</b>"
            )
        if scanner == "price_pump":
            return (
                f"• price_ratio_24h: <b>{metrics.get('price_ratio', 0.0):.3f}x</b>\n"
                f"• volume_24h_usd: <b>{metrics.get('volume_usd', 0.0):,.0f}</b>"
            )
        if scanner == "oi_spike":
            return (
                f"• oi_growth_pct: <b>{metrics.get('oi_growth_pct', 0.0):.2f}%</b>\n"
                f"• oi_usd: <b>{metrics.get('oi_usd', 0.0):,.0f}</b>\n"
                f"• price_growth_pct: <b>{metrics.get('price_growth_pct', 0.0):.2f}%</b>\n"
                f"• avg_daily_vol_usd: <b>{metrics.get('avg_daily_vol_usd', 0.0):,.0f}</b>"
            )
        return "\n".join(f"• {escape(str(key))}: <b>{value}</b>" for key, value in metrics.items())

    def _format_message(self, signal: SignalEvent) -> str:
        symbol = escape(signal.symbol.canonical_symbol)
        scanner = escape(signal.scanner_id)
        exchange = escape(signal.symbol.exchange)
        timestamp_utc = signal.candle_close_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        link = self._binance_link(signal.symbol.canonical_symbol)
        metrics_block = self._format_metrics(signal)
        emoji = {"vol_spike": "📊", "price_pump": "🚀", "oi_spike": "🧲"}.get(signal.scanner_id, "🔔")
        return (
            f"{emoji} <b>Signal detected</b>\n"
            f"• scanner: <b>{scanner}</b>\n"
            f"• symbol: <b>{symbol}</b>\n"
            f"• exchange: <b>{exchange}</b>\n"
            f"• score: <b>{signal.score:.3f}</b>\n"
            f"• timeframe: <b>{escape(signal.timeframe)}</b>\n"
            f"• candle_close: <b>{timestamp_utc}</b>\n"
            f"{metrics_block}\n"
            f"• binance: <a href=\"{link}\">open futures</a>"
        )

    async def send_signal(self, chat_id: int, signal: SignalEvent) -> None:
        if self._bot is None:
            return
        await self._bot.send_message(chat_id=chat_id, text=self._format_message(signal), parse_mode="HTML", disable_web_page_preview=True)

    async def close(self) -> None:
        if self._bot is None:
            return
        await self._bot.shutdown()
