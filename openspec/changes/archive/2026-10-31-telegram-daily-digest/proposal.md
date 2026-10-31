## Why

The stock analysis pipeline runs daily at 19:00 SGT, scraping Reddit hype, extracting metrics and Form 4/Congressional filings, and evaluating actionable stock recommendations. However, users currently have to open the web dashboard or inspect logs to see the results. Introducing an automated Telegram daily digest delivers market intelligence directly to users' mobile devices immediately upon pipeline completion, with zero manual checking and zero extra subscription costs.

## What Changes

- Add a standalone Telegram notification service (`app/telegram_notifier.py`) utilizing Telegram's Bot API (`sendMessage`).
- Integrate Telegram dispatch into `run_analysis_pipeline()` in `backend/app/pipeline.py` immediately following report generation and persistence.
- Format a single consolidated daily digest summarizing all 5 analyzed stocks: rank, ticker symbol, recommendation badge (`BUY`/`SELL`/`HOLD`), live price, target price, smart money verdict, and the AI actionable insight.
- Support `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` environment variables in `backend/.env`.
- Gracefully skip notification (without breaking or failing the pipeline) if Telegram credentials are not configured or if network dispatch fails.

## Capabilities

### New Capabilities
- `telegram-notifier`: Formats and dispatches consolidated market intelligence reports to a designated Telegram chat/channel via Bot API upon pipeline completion.

### Modified Capabilities
<!-- None: existing scraper, researcher, and frontend capabilities remain unchanged -->

## Impact

- **Backend Code**:
  - New module `backend/app/telegram_notifier.py`.
  - Integration call at the conclusion of `backend/app/pipeline.py`.
- **Dependencies**: Zero new dependencies; utilizes existing `httpx` async client.
- **Environment**: Optional `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `backend/.env`.

