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
