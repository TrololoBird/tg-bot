from __future__ import annotations

import os
from pathlib import Path

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", "signals.sqlite3"))
SCAN_INTERVAL_SECONDS = int(os.getenv("SCAN_INTERVAL_SECONDS", os.getenv("SCAN_INTERVAL", "300")))

TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "").strip()
_default_chat_id_raw = os.getenv("TG_DEFAULT_CHAT_ID", os.getenv("TG_ADMIN_CHAT_ID", "")).strip()
TG_DEFAULT_CHAT_ID = int(_default_chat_id_raw) if _default_chat_id_raw else None

MIN_VOL_USD_LAST = float(os.getenv("MIN_VOL_USD_LAST", "20000000"))
MIN_VOL_RATIO = float(os.getenv("MIN_VOL_RATIO", "5.0"))
MIN_PRICE_RATIO = float(os.getenv("MIN_PRICE_RATIO", "1.30"))
MIN_PRICE_SCANNER_VOL_USD_24H = float(os.getenv("MIN_PRICE_SCANNER_VOL_USD_24H", os.getenv("MIN_PRICE_VOL_USD_24H", str(MIN_VOL_USD_LAST))))
PRICE_SCORE_MAX_RATIO = float(os.getenv("PRICE_SCORE_MAX_RATIO", "2.0"))

OI_DAYS = int(os.getenv("OI_DAYS", "30"))
OI_GROWTH_PCT = float(os.getenv("OI_GROWTH_PCT", "50"))

OI_MAX_PRICE_GROWTH_PCT = float(os.getenv("OI_MAX_PRICE_GROWTH_PCT", "50"))
OI_MIN_AVG_DAILY_VOL_USD = float(os.getenv("OI_MIN_AVG_DAILY_VOL_USD", "5000000"))
OI_SORT_BY = os.getenv("OI_SORT_BY", "oi_usd").strip().lower()
_ALLOWED_OI_SORT_MODES = {"oi_usd", "oi_contracts", "price_growth", "avg_daily_vol_usd"}
if OI_SORT_BY not in _ALLOWED_OI_SORT_MODES:
    OI_SORT_BY = "oi_usd"

ENABLED_EXCHANGES = [item.strip().lower() for item in os.getenv("ENABLED_EXCHANGES", "binance").split(",") if item.strip()]
SYMBOLS_CACHE_TTL_SECONDS = int(os.getenv("SYMBOLS_CACHE_TTL_SECONDS", "900"))
TOP_SYMBOLS_LIMIT = int(os.getenv("TOP_SYMBOLS_LIMIT", "200"))

ADAPTER_RETRY_ATTEMPTS = int(os.getenv("ADAPTER_RETRY_ATTEMPTS", "3"))
ADAPTER_RETRY_BASE_DELAY_SECONDS = float(os.getenv("ADAPTER_RETRY_BASE_DELAY_SECONDS", "1.0"))
ADAPTER_TIMEOUT_MS = int(os.getenv("ADAPTER_TIMEOUT_MS", "10000"))

KNOWN_QUOTE_ASSETS = tuple(
    item.strip().upper()
    for item in os.getenv("KNOWN_QUOTE_ASSETS", "USDT,USDC,BUSD,FDUSD,DAI,TUSD,PAX,USDP").split(",")
    if item.strip()
)
