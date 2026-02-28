# tg-bot / combined_bot

Проект приведён к единой пакетной архитектуре `combined_bot`.

## Структура

```text
combined_bot/
  __init__.py
  main.py
  config.py
  models.py
  adapters/
    base.py
    binance.py
  scanners/
    __init__.py
    base.py
    volume.py
    price.py
    oi.py
    ml.py
  core/
    database.py
    orchestrator.py
  delivery/
    telegram_dispatcher.py
README.md
requirements.txt
.gitignore
```

## Что важно

- Источники реальных данных сейчас заглушены: `BinanceFuturesAdapter` возвращает пустые результаты.
- Для продакшн-использования нужно реализовать адаптеры с сетевым доступом (HTTP/WebSocket, retry, rate-limit, таймауты).
- Состояние и дедупликация сигналов хранятся в SQLite (`combined_bot/core/database.py`), JSON-файлы не используются.
- Heartbeat-рассылки пользователям отсутствуют.
- Загрузка pickle-модели в ML-сканере выполняется только при наличии и совпадении SHA-256 хэша.

## Запуск

1. Python 3.10+
2. Установить зависимости:

```bash
pip install -r requirements.txt
```

3. Запустить:

```bash
python -m combined_bot.main
```


## Переменные окружения (основные)

- `MIN_VOL_USD_LAST` — минимальный объём за последние 24 часа (USD).
- `MIN_VOL_RATIO` — минимальный коэффициент роста объёма (24ч к предыдущим 24ч).
- `MIN_PRICE_RATIO` — минимальный коэффициент роста цены за 24 часа.
- `OI_DAYS` — окно по open interest в днях.
- `OI_GROWTH_PCT` — минимальный прирост OI в процентах.
- `OI_MAX_PRICE_GROWTH_PCT` — максимальный допустимый рост цены для OI-сигнала.
- `OI_MIN_AVG_DAILY_VOL_USD` — минимальный средний дневной объём (USD) для OI-сигнала.

`MarketSymbol.from_raw()` нормализует символы в форматах CCXT: удаляет пробелы, берёт часть до `:`, поддерживает пары вида `BASE/QUOTE` и склеенные тикеры с `USDT`/`USDC` (например `BTC/USDT:USDT` → `BTC/USDT`).
