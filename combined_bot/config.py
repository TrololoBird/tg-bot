from __future__ import annotations

import os
from pathlib import Path

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", "signals.sqlite3"))
SCAN_INTERVAL_SECONDS = int(os.getenv("SCAN_INTERVAL", "300"))

MIN_VOL_USD_LAST = float(os.getenv("MIN_VOL_USD_LAST", "20000000"))
MIN_VOL_RATIO = float(os.getenv("MIN_VOL_RATIO", "5.0"))
MIN_PRICE_RATIO = float(os.getenv("MIN_PRICE_RATIO", "1.30"))

OI_DAYS = int(os.getenv("OI_DAYS", "30"))
OI_GROWTH_PCT = float(os.getenv("OI_GROWTH_PCT", "50"))

ENABLED_EXCHANGES = [item.strip() for item in os.getenv("ENABLED_EXCHANGES", "binance").split(",") if item.strip()]
