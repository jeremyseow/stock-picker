## Why

Currently, the "Historical Trends" section only displays an all-time aggregate mention count table from Reddit, which does not allow users to inspect past market intelligence reports by date. Users need the ability to select specific historical dates and view the full intelligence reports generated on those dates.

Additionally, investors and analysts have no unified view to monitor a single stock's trajectory across pipeline runs over time. Providing a dedicated ticker analytical report with historical time-series data (e.g. current price vs. target price chart, sentiment evolution, and recommendation changes) enables users to track whether analyst price targets and retail sentiment are converging or diverging.

Furthermore, isolated point-in-time daily reports lack multi-day synthesis. Adding an on-demand AI Trajectory Meta-Analysis (cached in the database) provides a longitudinal narrative that evaluates whether retail hype is diverging from fundamentals and whether previous catalysts and watchpoints played out.

## What Changes

- **Backend API Additions & Refinements**:
  - Add `/api/reports/dates` to fetch all distinct dates where analysis reports were generated.
  - Update `/api/reports` (or query parameters `?date=YYYY-MM-DD`) to fetch all stock reports generated on a selected date.
  - Add `/api/analytics/tickers` to return a list of all distinct tickers that have generated reports in the database.
  - Add `/api/analytics/ticker/{ticker}` returning full historical time-series data for that ticker: dates, current price, target price, recommendations, community sentiment, risk scores, and actionable insights.
  - Add `/api/analytics/ticker/{ticker}/meta-analysis` (POST/GET with optional force_refresh) providing an on-demand, SQLite-cached AI meta-analysis synthesizing multi-day trajectory, sentiment-vs-price divergence, and catalyst follow-through using Gemini.
- **Frontend Navigation & Page Enhancements**:
  - **Historical Reports**: Rename and transform the "Historical Trends" route (`/stats`) into a "Historical Reports" view with an interactive date selector to view full report cards for any past date.
  - **Ticker Analytics View**: Introduce a new route (`/analytics`) where users can select any tracked ticker and view its analytical overview:
    - Interactive time-series chart plotting historical Current Price vs. Target Price over time.
    - Historical Recommendation & Sentiment Timeline (BUY/HOLD/SELL badges, sentiment scores).
    - Fundamental Metrics Evolution (P/E ratios, 52-week range progression).
    - Historical Actionable Insights Log (chronological list of catalysts, findings, and risk assessments).
    - AI Trajectory Meta-Analysis Card with on-demand generation and cached recall (highlighting retail divergence and catalyst follow-through).
  - Update top navigation bar to include `Dashboard`, `Historical Reports`, and `Ticker Analytics`.

## Capabilities

### New Capabilities
- `ticker-analytics`: Multi-run time-series analytics for tracked tickers, including backend time-series API endpoints, SQLite-cached AI trajectory meta-analysis, and frontend chart visualization of current price vs. target price, sentiment evolution, and thesis milestones over time.

### Modified Capabilities
- `dashboard-frontend`: Replace the static mention ranking page with a date-based historical report browser, and update shared navigation header links.

## Impact

- **Backend**:
  - [`backend/app/models.py`](file:///g:/Users/Jeremy%20Seow/Side%20Projects/stock-picker/backend/app/models.py): New table/model `TickerTrajectoryAnalysis` to cache multi-run AI meta-analyses.
  - [`backend/app/llm_schemas.py`](file:///g:/Users/Jeremy%20Seow/Side%20Projects/stock-picker/backend/app/llm_schemas.py): Schema for structured trajectory meta-analysis output.
  - [`backend/app/agent.py`](file:///g:/Users/Jeremy%20Seow/Side%20Projects/stock-picker/backend/app/agent.py): New agent/prompt for multi-day longitudinal trajectory synthesis.
  - [`backend/app/main.py`](file:///g:/Users/Jeremy%20Seow/Side%20Projects/stock-picker/backend/app/main.py): New endpoints for date-filtered reports, ticker time-series analytics, and on-demand trajectory meta-analysis.
  - [`backend/app/crud.py`](file:///g:/Users/Jeremy%20Seow/Side%20Projects/stock-picker/backend/app/crud.py): Additional queries for distinct report dates, reports by date, distinct tickers, ticker history, and caching trajectory analysis.
- **Frontend**:
  - [`frontend/src/app/stats/page.tsx`](file:///g:/Users/Jeremy%20Seow/Side%20Projects/stock-picker/frontend/src/app/stats/page.tsx): Date picker and historical report cards.
  - New page `frontend/src/app/analytics/page.tsx`: Ticker selection, price vs target price chart, analytics timeline, and AI Trajectory Summary card.
  - [`frontend/src/app/page.tsx`](file:///g:/Users/Jeremy%20Seow/Side%20Projects/stock-picker/frontend/src/app/page.tsx) & layout: Updated navigation bar.
