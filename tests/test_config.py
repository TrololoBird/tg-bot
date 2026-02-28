import importlib


def test_oi_sort_by_invalid_value_falls_back_to_default(monkeypatch) -> None:
    monkeypatch.setenv("OI_SORT_BY", "unknown_mode")
    import combined_bot.config as config

    importlib.reload(config)
    assert config.OI_SORT_BY == "oi_usd"


def test_legacy_price_volume_env_alias(monkeypatch) -> None:
    monkeypatch.delenv("MIN_PRICE_SCANNER_VOL_USD_24H", raising=False)
    monkeypatch.setenv("MIN_PRICE_VOL_USD_24H", "123")
    import combined_bot.config as config

    importlib.reload(config)
    assert config.MIN_PRICE_SCANNER_VOL_USD_24H == 123
