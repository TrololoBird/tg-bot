from datetime import datetime, timezone

from combined_bot.delivery.telegram_dispatcher import TelegramDispatcher
from combined_bot.models import MarketSymbol, SignalEvent


def test_telegram_dispatcher_formats_volume_signal_message() -> None:
    dispatcher = TelegramDispatcher(token="")
    signal = SignalEvent(
        scanner_id="vol_spike",
        symbol=MarketSymbol.from_raw("binance", "BTC/USDT:USDT", market_type="linear_perp"),
        timeframe="1h",
        detected_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        candle_close_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        score=0.77,
        metrics={"prev_24h_volume_usd": 1_000_000, "last_24h_volume_usd": 6_000_000, "ratio": 6.0},
    )

    message = dispatcher._format_message(signal)

    assert "BTC/USDT" in message
    assert "vol_spike" in message
    assert "open futures" in message
    assert "6.00x" in message
