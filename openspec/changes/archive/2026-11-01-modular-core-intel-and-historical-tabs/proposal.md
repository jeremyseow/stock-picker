## Why

Currently, Engine 1 (Retail Momentum) and Engine 2 (Smart Money Scout) research stocks asymmetrically: retail stocks receive a rich four-pillar report with SEC EDGAR filings, news events, and risk scores, while Smart Money stocks receive an inflow ledger and political thesis but lack fundamental grounding (balance sheet health, 10-Q/8-K sanity checks, and financial ratios). Furthermore, historical run reporting (`/stats`) is restricted to Engine 1 retail reports, preventing users from reviewing past Smart Money discoveries or historical Synthesis Matrix archetypes.

Decoupling fundamental research into a reusable Core Equity Intel module ensures information parity across all discovered tickers, eliminates duplicate research when stocks overlap between engines, and powers a tabbed historical archive and unified report view.

## What Changes

- **Core Equity Intel Module**: Create a reusable fundamental research engine that analyzes SEC filings (10-K/10-Q/8-K), recent news headlines, and valuation ratios using Gemini for all candidate tickers across both engines (up to 10 unique stocks).
- **Normalized Multi-Tier Database Models**: Refactor the database schema to store `CoreEquityIntel`, `RetailReport`, `SmartMoneyReport`, and `SynthesisRecord` cleanly with foreign-key relationships.
- **Tabbed Historical Reports Archive (`/stats`)**: Update the historical reports view with a 3-tab layout (`Retail Momentum (N)`, `Smart Money & Gov (N)`, `Synthesis Matrix (N)`), date selector, and graceful empty states for missing engine runs.
- **Unified Master Report Page (`/report/[ticker]`)**: Upgrade the stock report view to dynamically render Core Fundamentals, the Retail Momentum overlay (or stealth notice), the Smart Money Inflow overlay (or no-cluster notice), and the Synthesis Archetype diagnosis.
- **Historical Archetype Trajectory in `/analytics`**: Add an archetype lifecycle progression timeline to Ticker Analytics showing how a stock migrated between archetypes over time.
- **Clean Database Reset & Execution**: Update `reset_and_run.py` to wipe and regenerate the normalized dual-engine pipeline end-to-end.

## Capabilities

### New Capabilities
- `core-equity-intel`: Shared fundamental research engine performing SEC 10-Q/8-K analysis, news retrieval, valuation ratio parsing, and Gemini-driven ground truth sanity checking for all candidate tickers.

### Modified Capabilities
- `dashboard-frontend`: Tabbed `/stats` historical reports view with badge counts, unified master report page rendering core intel with dynamic overlays, and archetype trajectory timeline in `/analytics`.
- `smart-money-scout`: Leverages shared Core Equity Intel for corporate fundamentals and attaches specialized insider cluster and political inflow overlays.
- `cross-engine-synthesis`: Adds historical date-based query support for archetype snapshots and correlates the unified candidate pool.

## Impact

- **Backend**: New module `backend/app/core_intel_engine.py`, updated `backend/app/models.py`, `backend/app/crud.py`, `backend/app/pipeline.py`, `backend/app/smart_money_pipeline.py`, and `backend/app/main.py`.
- **Database**: Clean migration/re-initialization of SQLite tables via `backend/scripts/reset_and_run.py`.
- **Frontend**: Updated `frontend/src/app/stats/page.tsx`, `frontend/src/app/report/[ticker]/page.tsx`, `frontend/src/app/analytics/page.tsx`, and supporting components.

