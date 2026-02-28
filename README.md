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
- Heartbeat-рассылки пользователям пока не реализованы и не настраиваются через env-переменные.
- `TelegramDispatcher` в текущем виде — stub.
- ML-сканер оставлен как экспериментальный модуль, но по умолчанию не включён в пользовательские настройки.

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

## Переменные окружения

### Общие

- `LOG_LEVEL` — уровень логирования (`INFO` по умолчанию).
- `DATABASE_PATH` — путь к SQLite-файлу (`signals.sqlite3` по умолчанию).
- `SCAN_INTERVAL_SECONDS` — интервал между итерациями сканирования в секундах (`300` по умолчанию).
- `SCAN_INTERVAL` — legacy-алиас для `SCAN_INTERVAL_SECONDS`.
- `ENABLED_EXCHANGES` — включённые биржи через запятую (`binance` по умолчанию).

### Разбор символов

- `KNOWN_QUOTE_ASSETS` — список суффиксов quote-актива через запятую для тикеров вида `BTCUSDT`.
  По умолчанию: `USDT,USDC,BUSD,FDUSD,DAI,TUSD,PAX,USDP`.

### Volume scanner

- `MIN_VOL_USD_LAST` — минимальный объём за последние 24 часа (USD).
- `MIN_VOL_RATIO` — минимальный коэффициент роста объёма (24ч к предыдущим 24ч).

### Price scanner

- `MIN_PRICE_RATIO` — минимальный коэффициент роста цены за 24 часа.
- `MIN_PRICE_SCANNER_VOL_USD_24H` — минимальный 24ч-объём (USD) для price-сканера.
- `MIN_PRICE_VOL_USD_24H` — legacy-алиас для `MIN_PRICE_SCANNER_VOL_USD_24H`.
- `PRICE_SCORE_MAX_RATIO` — коэффициент цены, при котором score достигает 1.0 (`2.0` по умолчанию).

### Open interest scanner

- `OI_DAYS` — окно по open interest в днях.
- `OI_GROWTH_PCT` — минимальный прирост OI в процентах.
- `OI_MAX_PRICE_GROWTH_PCT` — максимальный допустимый рост цены для OI-сигнала.
- `OI_MIN_AVG_DAILY_VOL_USD` — минимальный средний дневной объём (USD) для OI-сигнала.
- `OI_SORT_BY` — сортировка OI-сигналов: `oi_usd` (или любое неизвестное значение), `oi_contracts`, `price_growth`, `avg_daily_vol_usd`.

Пример запуска:

```bash
LOG_LEVEL=DEBUG \
DATABASE_PATH=./data/signals.sqlite3 \
SCAN_INTERVAL_SECONDS=180 \
ENABLED_EXCHANGES=binance \
MIN_VOL_USD_LAST=20000000 \
MIN_PRICE_SCANNER_VOL_USD_24H=15000000 \
KNOWN_QUOTE_ASSETS=USDT,USDC,BUSD,FDUSD,DAI,TUSD,PAX,USDP \
OI_SORT_BY=price_growth \
python -m combined_bot.main
```

`MarketSymbol.from_raw()` нормализует символы в форматах CCXT: удаляет пробелы, сохраняет исходный `raw_symbol` (в верхнем регистре) и отдельно разбирает торгуемую пару до `:` для `base/quote` (например `BTC/USDT:USDT`).
