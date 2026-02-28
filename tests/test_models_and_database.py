from datetime import datetime, timedelta, timezone
from pathlib import Path

from combined_bot.core.database import Database
from combined_bot.models import MarketSymbol, SignalEvent, UserSettings
from combined_bot.scanners.oi import OpenInterestScanner
from combined_bot.scanners.volume import VolumeSpikeScanner


def test_market_symbol_parses_extended_known_quote_suffix() -> None:
    symbol = MarketSymbol.from_raw("binance", "btctusd")
    assert symbol.base_asset == "BTC"
    assert symbol.quote_asset == "TUSD"


def test_market_symbol_keeps_canonical_symbol_for_colon_suffix() -> None:
    symbol = MarketSymbol.from_raw("binance", "BTC/USDT:USDT", market_type="linear_perp")
    assert symbol.raw_symbol == "BTC/USDT:USDT"
    assert symbol.canonical_symbol == "BTC/USDT"


def test_signal_dedup_key_uses_canonical_symbol() -> None:
    ts = datetime(2025, 1, 1, tzinfo=timezone.utc)
    signal_a = SignalEvent(
        scanner_id="vol_spike",
        symbol=MarketSymbol.from_raw("binance", "BTC/USDT"),
        timeframe="1h",
        detected_at=ts,
        candle_close_at=ts,
    )
    signal_b = SignalEvent(
        scanner_id="vol_spike",
        symbol=MarketSymbol.from_raw("binance", "BTC/USDT:USDT"),
        timeframe="1h",
        detected_at=ts,
        candle_close_at=ts,
    )
    assert signal_a.dedup_key == signal_b.dedup_key


def test_user_settings_normalize_case_and_blacklist() -> None:
    settings = UserSettings(
        chat_id=1,
        enabled_scanners=["Price_Pump", " OI_SPIKE "],
        enabled_exchanges=["BINANCE", " ByBit "],
        blacklist_symbols=[" BTC/USDT:USDT ", "eth/usdt"],
    )
    assert settings.enabled_scanners == ["price_pump", "oi_spike"]
    assert settings.enabled_exchanges == ["binance", "bybit"]
    assert settings.blacklist_symbols == ["BTC/USDT", "ETH/USDT"]


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


def test_oi_scanner_sort_oi_usd_mode_uses_price_multiplier(monkeypatch) -> None:
    monkeypatch.setattr("combined_bot.config.OI_SORT_BY", "oi_usd")
    scanner = OpenInterestScanner()
    assert scanner._sort_value(oi_end=10, avg_daily_vol_usd=1000, price_growth_pct=20, end_close=250) == 2500


def test_drop_open_candle_excludes_unclosed_1h(monkeypatch) -> None:
    scanner = VolumeSpikeScanner()
    monkeypatch.setattr("combined_bot.scanners.base.datetime", _FixedDateTime)
    candles = [
        [int(datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc).timestamp() * 1000), 0, 0, 0, 1, 1],
        [int(datetime(2025, 1, 1, 11, 0, tzinfo=timezone.utc).timestamp() * 1000), 0, 0, 0, 1, 1],
    ]
    filtered = scanner._drop_open_candle(candles, "1h")
    assert len(filtered) == 1


class _FixedDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return datetime(2025, 1, 1, 11, 30, tzinfo=tz or timezone.utc)
