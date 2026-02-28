"""Configuration parameters for the unified crypto signal bot.

At runtime the configuration values may be overridden via environment
variables. All configuration values defined here should be simple
constants that are loaded at import time. Avoid performing any I/O in
this module.

The user should set their Telegram bot token and any desired API keys in
the environment before running the bot. See the ``README.md`` for
detailed instructions.
"""

import os
from typing import Optional


# Telegram bot token (required for sending messages). At startup the
# orchestrator will raise a RuntimeError if this value is empty. In this
# skeleton we do not send real messages; the dispatcher will simply log
# messages instead.
TELEGRAM_TOKEN: str = os.getenv("TG_TOKEN", "")

# Proxy configuration for situations where the Telegram API must be
# accessed through an HTTP proxy. Leaving these fields blank disables
# proxying. See https://core.telegram.org/bots/faq#how-do-i-set-up-a-proxy
# for details.
PROXY_HOST: str = os.getenv("PROXY_HOST", "")
PROXY_PORT: str = os.getenv("PROXY_PORT", "")
PROXY_USER: str = os.getenv("PROXY_USER", "")
PROXY_PASS: str = os.getenv("PROXY_PASS", "")

# Log level for the entire application. Accepts the standard Python
# logging levels ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"). The
# default is "INFO".
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

# Database file path. SQLite will create this file on first run. For
# production deployments you may choose to point this at PostgreSQL or
# another SQL database, in which case you will need to modify
# ``core/database.py`` accordingly.
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./signals.db")

# Default scanning intervals. Each scanner may override these values
# internally if required. The units are seconds.
DEFAULT_SCAN_INTERVAL_SECONDS: int = int(os.getenv("SCAN_INTERVAL", "300"))

# Default minimum volume (USD) for a symbol to be considered by the
# volume and price scanners. Values are expressed in US dollars. These
# thresholds help filter out illiquid markets and reduce noise.
MIN_VOL_USD_LAST: float = float(os.getenv("MIN_VOL_USD_LAST", "20000000"))
MIN_VOL_RATIO: float = float(os.getenv("MIN_VOL_RATIO", "5.0"))
MIN_PRICE_RATIO: float = float(os.getenv("MIN_PRICE_RATIO", "1.30"))

# Open interest scanning parameters. These values control how far back
# to look and the minimum change required to trigger a signal. For more
# details see the documentation in ``scanners/oi.py``.
OI_DAYS: int = int(os.getenv("OI_DAYS", "30"))
OI_GROWTH_PCT: float = float(os.getenv("OI_GROWTH_PCT", "50"))

# Heartbeat interval in seconds. Heartbeats are sent only to the admin
# channel and not to end users. This helps detect if the bot is still
# alive without spamming subscribers. A value of 0 disables heartbeats.
HEARTBEAT_INTERVAL: int = int(os.getenv("HEARTBEAT_INTERVAL", "3600"))

# List of supported exchanges. In a production environment these might
# correspond to CCXT exchange ids. In this skeleton we include only
# "binance" to simplify implementation; additional adapters can be
# registered at runtime.
ENABLED_EXCHANGES: str = os.getenv("ENABLED_EXCHANGES", "binance")


def proxy_url() -> Optional[str]:
    """Construct a proxy URL if host and port are set.

    Returns ``None`` when no proxy should be used.
    """
    if PROXY_HOST and PROXY_PORT:
        if PROXY_USER and PROXY_PASS:
            return f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
        return f"http://{PROXY_HOST}:{PROXY_PORT}"
    return None