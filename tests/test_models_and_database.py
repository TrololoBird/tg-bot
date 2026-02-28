from datetime import datetime, timedelta, timezone
from pathlib import Path

from combined_bot.core.database import Database
from combined_bot.models import MarketSymbol, SignalEvent, UserSettings


def test_market_symbol_parses_extended_known_quote_suffix() -> None:
    symbol = MarketSymbol.from_raw("binance", "btctusd")
    assert symbol.base_asset == "BTC"
    assert symbol.quote_asset == "TUSD"


def test_user_settings_default_scanners_do_not_include_ml() -> None:
    settings = UserSettings(chat_id=1)
    assert settings.enabled_scanners == ["vol_spike", "price_pump", "oi_spike"]


def test_database_dedup_uses_unix_timestamps_and_prunes_expired(tmp_path: Path) -> None:
    database = Database(tmp_path / "data" / "signals.sqlite3")
    signal = SignalEvent(
        scanner_id="vol_spike",
        symbol=MarketSymbol.from_raw("binance", "BTC/USDT"),
        timeframe="1h",
        detected_at=datetime.now(timezone.utc),
        candle_close_at=datetime.now(timezone.utc),
    )
    database.remember_signal(signal)
    assert database.is_duplicate(signal)

    expired = int((datetime.now(timezone.utc) - timedelta(seconds=60)).timestamp())
    with database._connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO signal_dedup(dedup_key, expires_at) VALUES (?, ?)",
            ("expired-key", expired),
        )
        row = conn.execute("SELECT expires_at FROM signal_dedup WHERE dedup_key = ?", ("expired-key",)).fetchone()
    assert isinstance(row["expires_at"], int)

    database.prune_expired_dedup(force=True)
    with database._connect() as conn:
        row = conn.execute("SELECT dedup_key FROM signal_dedup WHERE dedup_key = ?", ("expired-key",)).fetchone()
    assert row is None
