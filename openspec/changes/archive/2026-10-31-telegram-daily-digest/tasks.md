## 1. Telegram Notifier Service

- [x] 1.1 Create `backend/app/telegram_notifier.py` with `format_daily_digest(reports)` and `send_daily_digest(reports)`.
- [x] 1.2 Implement HTML message formatting with recommendation badges (BUY 🟢, SELL 🔴, HOLD 🟡), live vs target prices, upside percentages, and Smart Money verdicts.
- [x] 1.3 Add credential validation (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`) and fault-tolerant exception handling so delivery failures never disrupt pipeline execution.

## 2. Pipeline Integration

- [x] 2.1 Update `backend/app/pipeline.py` to collect saved reports and ticker summaries during execution.
- [x] 2.2 Add Step 6 to `run_analysis_pipeline()` invoking `await send_daily_digest(reports)`.

## 3. Verification & Documentation

- [x] 3.1 Add automated test suite in `backend/tests/test_telegram_notifier.py` covering digest formatting, mock HTTP transmission, and unconfigured environment handling.
- [x] 3.2 Update `README.md` and `backend/README.md` with instructions on creating a Telegram bot with `@BotFather` and configuring `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`.

