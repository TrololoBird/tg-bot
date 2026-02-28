import asyncio
import pytest

pytest.importorskip("ccxt.async_support")

from combined_bot.adapters.binance import BinanceFuturesAdapter
from combined_bot.core.orchestrator import Orchestrator
from combined_bot.models import UserSettings


class _DummyScanner:
    id = "dummy"

    async def scan(self, adapters):
        _ = adapters
        return []


class _DummyDatabase:
    def get_active_user_settings(self):
        return [UserSettings(chat_id=1)]

    def is_duplicate(self, signal):
        _ = signal
        return False

    def remember_signal(self, signal):
        _ = signal


class _DummyDispatcher:
    def __init__(self):
        self.closed = False

    async def send_signal(self, chat_id, signal):
        _ = chat_id, signal

    async def close(self):
        self.closed = True


class _DummyAdapter:
    def __init__(self):
        self.closed = False

    async def list_symbols(self):
        return []

    async def fetch_ohlcv(self, symbol, timeframe, limit):
        _ = symbol, timeframe, limit
        return []

    async def fetch_open_interest_history(self, symbol, days):
        _ = symbol, days
        return []

    async def close(self):
        self.closed = True


@pytest.mark.asyncio
async def test_orchestrator_run_closes_adapters_and_dispatcher_on_cancel():
    adapter = _DummyAdapter()
    dispatcher = _DummyDispatcher()
    orchestrator = Orchestrator(
        adapters={"binance": adapter},
        scanners=[_DummyScanner()],
        database=_DummyDatabase(),
        dispatcher=dispatcher,
        interval_seconds=60,
    )

    task = asyncio.create_task(orchestrator.run())
    await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert adapter.closed is True
    assert dispatcher.closed is True


@pytest.mark.asyncio
async def test_binance_list_symbols_keeps_only_usdt_linear_swap():
    adapter = BinanceFuturesAdapter()

    class _Client:
        def __init__(self):
            self.markets = {
                "BTCUSDT": {"symbol": "BTC/USDT:USDT", "active": True, "swap": True, "linear": True, "quote": "USDT"},
                "ETHUSDC": {"symbol": "ETH/USDC:USDC", "active": True, "swap": True, "linear": True, "quote": "USDC"},
            }

        async def load_markets(self):
            return None

        async def close(self):
            return None

    adapter._client = _Client()
    adapter._markets_loaded = False

    symbols = await adapter.list_symbols()
    await adapter.close()

    assert symbols == ["BTC/USDT:USDT"]
