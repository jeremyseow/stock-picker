## Context

See `proposal.md` for background and motivation.
The system currently collects basic metrics, SEC filings (10-K, 10-Q, 8-K), and general news before prompting Gemini 2.5 Pro via Pydantic AI. The user interface displays a 4-pillar analysis but lacks visibility into whether corporate executives (Form 4) and politicians (STOCK Act) are trading alongside or against retail sentiment.

## Goals / Non-Goals

**Goals:**
- Extract 6-month aggregate insider purchases/sales and recent Form 4 transactions natively using `yfinance`.
- Extract recent Congressional/Senate trading disclosures using targeted DuckDuckGo search queries.
- Expand `StockReport` schema to include `smart_money_verdict` and `insider_activity_summary`.
- Enforce strict recommendation rules in the LLM prompt: heavy insider net selling restricts ratings from `BUY` to `HOLD` or `SELL`.
- Persist `raw_insider_data` and `smart_money_verdict` in `TickerReport`.
- Build a dedicated, responsive "Smart Money & Insider Trading Radar" UI panel on the frontend report page (`/report/[ticker]`).

**Non-Goals:**
- Subscribing to paid financial APIs (e.g., Bloomberg, Quiver Quantitative); utilize zero-cost native `yfinance` data and web search.
- Scraping non-US foreign market insider filings.

## Decisions

### 1. Zero-Cost Insider & Congressional Data Pipeline
- **Decision**: 
  - Use `yfinance`'s `insider_purchases` (6-month aggregate volume, purchases vs sales, net shares) and `insider_transactions` (recent executive trades).
  - Use `ddgs` (DuckDuckGo) with query `f"{ticker} stock congressional trading disclosure representative senator purchase sale"` for political trades.
- **Rationale**: Requires no new third-party credentials or recurring costs, integrates immediately into existing async pipeline helpers, and provides clean data for all US equities.
- **Alternatives Considered**: Direct EDGAR XML scraping (high complexity and brittle parsing) or paid API subscriptions.

### 2. Pydantic Schema and Prompt Guardrails
- **Decision**:
  - Add `smart_money_verdict: str` (e.g. "Bearish Divergence", "Bullish Accumulation", "Neutral Distribution") and `insider_activity_summary: str` to `StockReport`.
  - Add explicit negative constraints in the agent prompt: If Form 4 disclosures reveal substantial net insider selling (> $10M or key C-suite liquidation), the model MUST NOT issue a "BUY" recommendation, even if social sentiment is overwhelmingly bullish.
- **Rationale**: Directly addresses the "buying into C-suite distribution" trap that retail investors frequently fall into.

### 3. Database Schema Evolution
- **Decision**: Add `smart_money_verdict = Column(String)` and `raw_insider_data = Column(JSON)` to `TickerReport` in `backend/app/models.py`.
- **Rationale**: Preserves raw transactions for fast frontend rendering while storing the synthesized verdict for query endpoints and analytics.

### 4. Frontend Component Design
- **Decision**: Add a dedicated `SmartMoneyRadar` section to `/report/[ticker]` featuring:
  - 6-Month Net Flow gauge (visualizing purchases vs. sales ratio).
  - Structured Form 4 recent filings table (Date, Insider, Role, Shares, Value, Transaction Type).
  - Congressional & Senate trade disclosure callout.
  - AI Smart Money Divergence verdict callout.
- **Rationale**: Places institutional context directly beside retail sentiment so users can immediately contrast hype with insider behavior.

## Risks / Trade-offs

- **[Missing Insider Filings for Certain Tickers]** → Foreign companies or certain OTC stocks may have None/empty `insider_transactions`.
  - *Mitigation*: The backend data collector checks for `None` or empty DataFrames, returning safe structured defaults (`{"has_data": False, "summary": "No Form 4 filings recorded"}`). The UI shows a graceful neutral fallback card.
- **[Routine 10b5-1 Trading Plans]** → Executive sales are often pre-scheduled routine transactions.
  - *Mitigation*: The prompt instructs the LLM to differentiate between routine planned exercises and opportunistic cluster selling or significant net accumulation.

