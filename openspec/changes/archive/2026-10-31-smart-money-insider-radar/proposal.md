## Why

Retail investors on Reddit frequently chase momentum stocks at or near market peaks without visibility into whether corporate insiders (CEOs, CFOs, Board Directors) or politicians are aggressively selling or quietly accumulating shares.

Integrating SEC Form 4 insider transaction flows and Congressional STOCK Act disclosure tracking directly into the research pipeline equips investors with "Smart Money" sanity checks, preventing retail from buying into heavy insider distribution and identifying institutional alignment.

## What Changes

- **Backend Ingestion & Research Enhancement**:
  - Enrich `market_researcher.py` to query `yfinance` for:
    - 6-month aggregate insider purchases, sales, and net shares (`insider_purchases`).
    - The latest detailed Form 4 insider transactions (Date, Insider Name, Position, Shares, Value, Transaction Type).
  - Target DuckDuckGo search queries for recent Congressional & Senate stock disclosures.
  - Update `llm_schemas.py` and `agent.py` to incorporate a dedicated `smart_money_analysis` section into `StockReport`, instructing Gemini to flag divergences (e.g. retail hype vs. heavy insider dumping) and forbid BUY ratings when C-suite executives are aggressively selling.
  - Persist `raw_insider_data` in `TickerReport`.
- **Frontend Report Enhancement**:
  - Add a dedicated **Smart Money & Insider Trading Radar** panel to `/report/[ticker]`:
    - 6-month net insider flow gauge (Net Buying vs. Net Selling).
    - Recent Form 4 transactions table with executive names, roles, values, and transaction badges.
    - Congressional and Senate trade disclosure highlights.
    - AI Smart Money Divergence summary.
  - Display insider activity badges/indicators where appropriate on the dashboard and ticker analytics views.

## Capabilities

### Modified Capabilities
- `market-researcher`: Extend data gathering to include SEC Form 4 insider transaction statistics and Congressional disclosures, incorporating smart-money divergence reconciliation into the structured LLM prompt and recommendation logic.
- `dashboard-frontend`: Add the Smart Money & Insider Trading Radar panel to the individual stock intel report view.

## Impact

- **Backend**:
  - [`backend/app/market_researcher.py`](file:///g:/Users/Jeremy%20Seow/Side%20Projects/stock-picker/backend/app/market_researcher.py): New data collection functions for insider purchases, transactions, and congressional trade searches.
  - [`backend/app/llm_schemas.py`](file:///g:/Users/Jeremy%20Seow/Side%20Projects/stock-picker/backend/app/llm_schemas.py): Schema update for `StockReport` to include `smart_money_verdict` and `insider_activity_summary`.
  - [`backend/app/agent.py`](file:///g:/Users/Jeremy%20Seow/Side%20Projects/stock-picker/backend/app/agent.py): System prompt update enforcing insider selling guardrails on recommendations.
  - [`backend/app/models.py`](file:///g:/Users/Jeremy%20Seow/Side%20Projects/stock-picker/backend/app/models.py): Storage for insider data and verdicts in `ticker_reports`.
  - [`backend/app/pipeline.py`](file:///g:/Users/Jeremy%20Seow/Side%20Projects/stock-picker/backend/app/pipeline.py): Pass insider data into the report generator.
- **Frontend**:
  - [`frontend/src/app/report/[ticker]/page.tsx`](file:///g:/Users/Jeremy%20Seow/Side%20Projects/stock-picker/frontend/src/app/report/[ticker]/page.tsx): Render the Smart Money & Insider Radar UI card with net flow gauge and transaction table.

