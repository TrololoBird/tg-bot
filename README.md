# Unified Crypto Signal Bot

This repository contains a reference implementation of a unified
cryptocurrency signal bot. It consolidates multiple disparate scripts
(volume pump, price pump, open interest scanner, etc.) into a single
extensible architecture. The primary goal of this project is to
illustrate clean separation of concerns and provide a starting point
for further development rather than deliver a fully functional
production system.

## Architecture

The code is organised into four logical layers:

1. **Adapters (Layer 1)** – Exchange adapters encapsulate API calls
   behind a common interface. They expose methods such as
   `list_symbols`, `fetch_ohlcv`, `fetch_ticker` and
   `fetch_open_interest_history`. The current implementation includes
   only a stub for Binance Futures. To integrate additional
   exchanges or enable real network access, subclass
   `BaseExchangeAdapter` and override its methods.

2. **Scanners (Layer 2)** – Scanners implement the logic for
   detecting interesting events in the market. Four scanners are
   provided:

   * `VolumeSpikeScanner` – detects 24‑hour volume growth of at least
     five times relative to the previous 24 hours.
   * `PricePumpScanner` – detects price increases of 30 % or more over
     the last 24 hours with sufficient trading volume.
   * `OpenInterestScanner` – detects significant increases in open
     interest and reports accompanying price and volume statistics.
   * `MachineLearningScanner` – demonstrates how a pretrained model
     could be used to predict pumps. It loads a pickle file on
     startup and evaluates a minimal feature set; replace this with
     proper feature engineering and model loading as needed.

3. **Core (Layer 3)** – The orchestrator coordinates scanning,
   deduplication, persistence and dispatching. It uses a simple
   SQLite database to store user settings and record which signals
   have already been sent. The orchestrator periodically runs each
   scanner and delivers deduplicated signals to subscribed chats.

4. **Delivery (Layer 4)** – The delivery layer currently consists of
   a stubbed Telegram dispatcher that logs messages to the console
   instead of sending them. When network access and the
   `python-telegram-bot` package are available, this can be
   extended to send real messages via the Telegram Bot API.

## Limitations

* **No network access:** The execution environment does not allow
  outbound HTTP requests. Consequently, the default adapters return
  empty data structures. To obtain real market data you must
  implement custom adapters that fetch from local caches or connect
  to exchanges in a permitted environment.
* **Missing external dependencies:** Packages such as `ccxt` and
  `python-telegram-bot` are not installed. The code is designed to
  run without them; however, some functionality (e.g. sending
  Telegram messages) is stubbed out.
* **Model loading:** The machine learning scanner loads a pickle
  model directly, which is generally unsafe. In a production
  system you should verify the model’s integrity (e.g. via a hash)
  and consider using a safer format like ONNX.

## Usage

1. Ensure you are using a Python 3.10+ environment.
2. Set the environment variable `TG_TOKEN` to your Telegram bot
   token if you intend to integrate with Telegram. Also set
   `ADMIN_CHAT_ID` to the chat id that should receive signals and
   heartbeats.
3. Install any missing dependencies if you wish to extend the
   adapters or the dispatcher.
4. Run the bot:

   ```bash
   python -m combined_bot.main
   ```

   The bot will start the orchestrator and periodically run the
   scanners. Detected signals will be logged to the console and
   recorded in the database.

## Extending the bot

* **Adding exchanges:** Implement a subclass of
  `BaseExchangeAdapter` that wraps the desired exchange’s API and
  return it in `combined_bot/main.py`.
* **Adding scanners:** Create a new module in
  `combined_bot/scanners` that derives from `BaseScanner` and
  implements the `scan` coroutine. Register it in
  `combined_bot/main.py`.
* **Improving delivery:** Replace the implementation in
  `combined_bot/delivery/telegram_dispatcher.py` with calls to
  `python-telegram-bot` or any other messaging service. Ensure that
  formatting complies with the target platform’s requirements.
