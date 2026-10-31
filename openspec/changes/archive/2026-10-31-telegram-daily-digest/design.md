## Context

See `proposal.md` for motivation and background.
The stock analysis pipeline runs daily at 19:00 SGT via APScheduler (or on-demand via `run_pipeline.py`). For each of the top 5 tickers, it evaluates Reddit sentiment, financial metrics, SEC Form 4 insider data, and Congressional disclosures, producing a `StockReport` saved to SQLite via `save_ticker_report()`.

## Goals / Non-Goals

**Goals:**
- Implement an async Telegram notification module (`app/telegram_notifier.py`) that formats and dispatches a consolidated daily market intelligence digest.
- Hook into `backend/app/pipeline.py` to trigger dispatch immediately after all reports in a run are persisted.
- Ensure 100% fault tolerance: if Telegram credentials are unset or the network fails, log appropriately and continue without disrupting pipeline execution.
- Format messages cleanly using Telegram HTML mode with emoji indicators for recommendations and Smart Money verdicts.

**Non-Goals:**
- Interactive two-way bot polling or webhooks (handling `/intel` user commands in Telegram chat is reserved for a future phase).
- Generating and uploading image charts or screenshots to Telegram.
- Third-party push notification services (e.g. Pushover, Discord, Slack).

## Decisions

### 1. Direct Telegram REST API via Existing `httpx`
- **Decision**: Make direct async POST calls to `https://api.telegram.org/bot<TOKEN>/sendMessage` using `httpx.AsyncClient()`.
- **Rationale**: `httpx` is already part of the project dependencies. Avoiding heavy wrapper libraries (like `python-telegram-bot` or `aiogram`) prevents version conflicts, keeps container footprints minimal, and requires zero background daemon threads.
- **Alternatives Considered**: `python-telegram-bot` (heavy dependency overhead for simple outbound message sending).

### 2. Telegram HTML Parse Mode over MarkdownV2
- **Decision**: Format messages using Telegram's HTML parse mode (`<b>`, `<i>`, `<code>`) rather than MarkdownV2.
- **Rationale**: Telegram's MarkdownV2 parser strictly requires backslash-escaping for 18 reserved characters (including `.`, `-`, `(`, `)`, `$`), which frequently breaks when formatting financial tickers, decimal percentages, and prices. HTML parse mode is reliable, straightforward, and eliminates formatting exceptions.
- **Alternatives Considered**: MarkdownV2 (high risk of escaping errors and 400 Bad Request responses).

### 3. Pipeline Step 6 Dispatch Hook
- **Decision**: In `pipeline.py`, collect the generated report summaries in a list during the ticker loop and call `await send_daily_digest(processed_reports)` as Step 6.
- **Rationale**: Consolidates all 5 ticker reports into a single cohesive digest rather than sending 5 separate noisy notifications.

## Risks / Trade-offs

- **[Telegram Message Length Limit (4,096 characters)]** → A 5-stock digest with summaries is approximately 1,000–1,500 characters.
  - *Mitigation*: Actionable insights and rationales are truncated to concise bullet points, well within the 4,096-character limit.
- **[Missing Credentials in CI / Local Dev]** → Developers without Telegram bots should be able to run tests and pipelines seamlessly.
  - *Mitigation*: `send_daily_digest` explicitly checks for `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`. If either is missing, it logs an informational message and returns without error.

