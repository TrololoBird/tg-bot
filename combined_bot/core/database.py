from __future__ import annotations

import json
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator, List

from ..models import SignalEvent, UserSettings


class Database:
    _PRUNE_INTERVAL_SECONDS = 3600

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._last_prune_at = 0.0
        self._init_db()
        self.prune_expired_dedup(force=True)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_settings (
                    chat_id INTEGER PRIMARY KEY,
                    is_active INTEGER NOT NULL,
                    enabled_scanners TEXT NOT NULL,
                    enabled_exchanges TEXT NOT NULL,
                    min_score_threshold REAL NOT NULL,
                    blacklist_symbols TEXT NOT NULL,
                    timezone TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS signal_dedup (
                    dedup_key TEXT PRIMARY KEY,
                    expires_at INTEGER NOT NULL
                )
                """
            )

    def upsert_user_settings(self, settings: UserSettings) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO user_settings(chat_id, is_active, enabled_scanners, enabled_exchanges, min_score_threshold, blacklist_symbols, timezone)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(chat_id) DO UPDATE SET
                    is_active=excluded.is_active,
                    enabled_scanners=excluded.enabled_scanners,
                    enabled_exchanges=excluded.enabled_exchanges,
                    min_score_threshold=excluded.min_score_threshold,
                    blacklist_symbols=excluded.blacklist_symbols,
                    timezone=excluded.timezone
                """,
                (
                    settings.chat_id,
                    int(settings.is_active),
                    json.dumps(settings.enabled_scanners),
                    json.dumps(settings.enabled_exchanges),
                    settings.min_score_threshold,
                    json.dumps(settings.blacklist_symbols),
                    settings.timezone,
                ),
            )

    def get_active_user_settings(self) -> List[UserSettings]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM user_settings WHERE is_active = 1").fetchall()
        return [
            UserSettings(
                chat_id=row["chat_id"],
                is_active=bool(row["is_active"]),
                enabled_scanners=json.loads(row["enabled_scanners"]),
                enabled_exchanges=json.loads(row["enabled_exchanges"]),
                min_score_threshold=row["min_score_threshold"],
                blacklist_symbols=json.loads(row["blacklist_symbols"]),
                timezone=row["timezone"],
            )
            for row in rows
        ]

    def prune_expired_dedup(self, force: bool = False) -> None:
        now_ts = int(datetime.now(timezone.utc).timestamp())
        now_monotonic = time.monotonic()
        if not force and now_monotonic - self._last_prune_at < self._PRUNE_INTERVAL_SECONDS:
            return
        with self._connect() as conn:
            conn.execute("DELETE FROM signal_dedup WHERE expires_at <= ?", (now_ts,))
        self._last_prune_at = now_monotonic

    def is_duplicate(self, signal: SignalEvent) -> bool:
        self.prune_expired_dedup()
        with self._connect() as conn:
            row = conn.execute("SELECT dedup_key FROM signal_dedup WHERE dedup_key = ?", (signal.dedup_key,)).fetchone()
        return row is not None

    def remember_signal(self, signal: SignalEvent) -> None:
        expires = datetime.now(timezone.utc) + timedelta(seconds=signal.ttl_seconds)
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO signal_dedup(dedup_key, expires_at) VALUES (?, ?)",
                (signal.dedup_key, int(expires.timestamp())),
            )
