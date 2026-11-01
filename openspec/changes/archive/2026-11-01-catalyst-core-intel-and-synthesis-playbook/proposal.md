## Why

Currently, when investigating a Smart Money candidate (like `$ACN` or `$TTMI`), the Smart Catalyst Report lacks fundamental ratios (P/E, market cap, 52-week range) and SEC 10-Q/8-K ground truth, instead providing a confusing link labeled "View Retail Report" even for non-retail stocks. Furthermore, navigating to the Master Report from the Synthesis Matrix feels redundant because it stacks the exact same four panels already viewed in earlier tabs. Finally, the API endpoints and frontend routes exhibit naming asymmetry (`/api/reports` vs. `/api/smart-money`).

This change embeds Core Equity Intelligence directly into the Smart Money Catalyst Report, elevates the Cross-Engine Synthesis Master Report into a high-alpha **Divergence Heatmap & Contrarian Playbook**, and harmonizes all API endpoints and route naming across both discovery engines.

## What Changes

- **Self-Contained Smart Catalyst Report (`/smart-money/[ticker]`)**:
  - Update `GET /api/smart-money/report/{ticker}` to return the linked `CoreEquityIntel` record alongside Form 4 inflows and committee hearings.
  - Embed the **Core Fundamentals & Ground Truth Grid** (valuation ratios, SEC filings synthesis, corporate positioning, events, and risk score) directly into `/smart-money/[ticker]`.
- **High-Value Synthesis Master Report & Contrarian Playbook (`/report/[ticker]`)**:
  - Introduce a **Divergence Heatmap / Quadrant Scorecard** visually comparing Retail Sentiment against Smart Money Conviction with a timing edge gauge.
  - Deliver an **Actionable Contrarian Execution Playbook** detailing specific execution tactics based on the market archetype (entry timing, swing catalyst horizon, and exit triggers).
  - Add an **Archetype Lifecycle Progression Vector** showing the stock's phase transition (`Silent Accumulation ➔ The Rocket ➔ The Retail Trap ➔ Market Noise`).
- **Consistent API Endpoints**:
  - Expose `/api/retail/reports` and `/api/retail/report/{ticker}` for Engine 1 (with `/api/reports` maintained as a backward-compatible alias).
  - Maintain `/api/smart-money/reports` and `/api/smart-money/report/{ticker}` for Engine 2.
  - Maintain `/api/synthesis/reports` and `/api/synthesis/latest` for Cross-Engine Synthesis.
  - Expose `/api/master/report/{ticker}` as an alias for the Unified Master Equity Report.

## Capabilities

### Modified Capabilities

- `smart-money-scout`: The Smart Money catalyst report SHALL embed linked Core Equity Intelligence (valuation ratios, SEC 10-Q/8-K analysis, risk profile), providing a self-contained fundamental evaluation.
- `cross-engine-synthesis`: The Cross-Engine Synthesis Master Report SHALL present a Divergence Heatmap comparing retail hype vs. institutional conviction and an Actionable Contrarian Execution Playbook tailored to the stock's market archetype.
- `dashboard-frontend`: The frontend dashboard SHALL present Core Fundamentals within the Smart Money detail view, render the Contrarian Execution Playbook in the Master Report, and consume consistently namespaced API endpoints.

## Impact

- **Backend**: `backend/app/main.py` adds namespaced `/api/retail/...` and `/api/master/...` routes and enriches `/api/smart-money/report/{ticker}` with Core Intel.
- **Frontend**: `frontend/src/app/smart-money/[ticker]/page.tsx` embeds the Core Intel grid; `frontend/src/app/report/[ticker]/page.tsx` renders the Divergence Heatmap & Contrarian Playbook.
- **Tests**: `backend/tests/` adds tests for the new endpoint aliases, enriched smart money payload, and playbooks.

