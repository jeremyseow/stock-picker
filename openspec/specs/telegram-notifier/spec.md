# telegram-notifier Specification

## Purpose
Dispatches automated, cleanly formatted Telegram daily market intelligence digests to subscribers upon the completion of the daily stock analysis pipeline.

## Requirements

### Requirement: Consolidated Daily Intelligence Digest
The system SHALL format and transmit a single consolidated market intelligence digest to a configured Telegram chat or channel whenever the daily stock analysis pipeline finishes executing.

#### Scenario: Dispatch Digest on Pipeline Completion
- **WHEN** the daily stock analysis pipeline finishes evaluating all candidate tickers
- **THEN** the system compiles a summary of all processed tickers and dispatches an HTML-formatted message to Telegram containing each ticker's rank, recommendation, current price, target price, upside percentage, smart money verdict, and immediate actionable insight.

### Requirement: Graceful Degradation When Unconfigured or Offline
The notification service SHALL verify the presence of Telegram credentials before attempting transmission, and SHALL NOT cause the pipeline run or scheduled job to fail if credentials are missing or if the Telegram API call fails.

#### Scenario: Unset Telegram Credentials
- **WHEN** `TELEGRAM_BOT_TOKEN` or `TELEGRAM_CHAT_ID` is missing from the environment
- **THEN** the system logs an informational message indicating that Telegram notifications are disabled, and cleanly completes the pipeline without throwing an exception.

#### Scenario: Telegram API Request Failure
- **WHEN** the Telegram Bot API endpoint returns an HTTP error code or network timeout
- **THEN** the system logs the error with details and allows the pipeline run to conclude successfully.

### Requirement: Rich Formatting and Smart Money Badges
The consolidated digest message SHALL use Telegram HTML formatting and emoji status indicators to visually differentiate BUY, SELL, and HOLD recommendations as well as Smart Money verdicts.

#### Scenario: Format Ticker Summary
- **WHEN** a stock report is rendered in the digest
- **THEN** it renders the ticker symbol with recommendation indicator (🟢 BUY, 🔴 SELL, 🟡 HOLD), current price vs target price, potential upside percentage, smart money alignment verdict, and the AI actionable insight in a concise bullet block.

