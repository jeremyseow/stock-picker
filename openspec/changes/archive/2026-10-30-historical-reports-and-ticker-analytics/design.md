## Context

See `proposal.md` for overall motivation.
Currently, the backend stores analysis records in SQLite (`ticker_reports` and `daily_tickers`) using SQLAlchemy async. Reports are generated per daily pipeline run. The frontend is a Next.js (App Router) client with Tailwind CSS, currently showing the latest run on `/` and a static mention table on `/stats`.

## Goals / Non-Goals

**Goals:**
- Provide backend endpoints to list distinct report dates and query all reports for any given date.
- Transform the frontend `/stats` page into a Historical Reports explorer where users can pick a date and browse report cards from that run.
- Provide backend endpoints to list all distinct tickers and retrieve time-series metrics for any chosen ticker.
- Add on-demand AI Trajectory Meta-Analysis (evaluating sentiment-vs-price divergence and catalyst follow-through) cached in SQLite.
- Create a dedicated `/analytics` page in the frontend featuring:
  - Ticker selector.
  - Interactive SVG line chart comparing historical Current Price vs. Target Price over time.
  - Recommendation & Sentiment progression timeline.
  - Key financial valuation trajectory (P/E ratios, 52-week ranges).
  - Chronological actionable insights log.
  - AI Trajectory Meta-Analysis card with generate/refresh button and cache badge.
- Update header navigation across all views.

**Non-Goals:**
- Intraday real-time tick streaming (reports are snapshot-based per pipeline run).
- Changes to the Reddit scraping, yfinance fetching, or daily pipeline execution schedule.

## Decisions

### 1. Zero-Dependency Responsive SVG Charting on Frontend
- **Decision**: Render time-series charts using pure SVG and Tailwind CSS within React rather than importing heavy charting libraries (like Chart.js or Recharts).
- **Rationale**: Keeps the Next.js client bundle minimal, avoids React 19/Next 15 peer dependency issues, and allows seamless styling consistent with the existing slate/indigo dark theme.
- **Alternatives Considered**: `recharts` or `chart.js` (adds external dependencies, SSR hydration quirks, and bundle bloat for relatively straightforward multi-series line charts).

### 2. Date Aggregation & Querying
- **Decision**: Use `func.date(TickerReport.date)` in SQLite to aggregate and list distinct dates as `YYYY-MM-DD`. The `/api/reports?date=YYYY-MM-DD` endpoint will query all reports where `func.date(TickerReport.date) == date`.
- **Rationale**: Isolates date matching cleanly regardless of whether pipeline runs fired at 19:00 or 20:00 UTC/local time, ensuring all tickers from that calendar date run are returned together.
- **Alternatives Considered**: Exact timestamp matching (too brittle if tickers within a single run are committed seconds apart).

### 3. Ticker Analytics Data Structure & AI Meta-Analysis Caching
- **Decision**: 
  - Endpoint `/api/analytics/ticker/{ticker}` returns an ordered array of historical snapshots.
  - Endpoint `/api/analytics/ticker/{ticker}/meta-analysis` generates/retrieves an AI meta-analysis structured as:
    - `divergence_analysis`: Divergence between retail hype and price action.
    - `catalyst_follow_through`: Evaluation of whether past actionable insights played out.
    - `trajectory_outlook`: Longitudinal outlook and stability of consensus.
  - Persisted in a new table `ticker_trajectory_analyses` linked to `(ticker, latest_report_id)`.
- **Rationale**: Keeps the initial page load instant, and avoids burning LLM tokens on repeated visits unless new report data exists or the user clicks "Refresh Analysis".

### 4. Complementary Components in Analytical Report
To deliver the most valuable analytical experience, the `/analytics` view will display:
1. **Current vs. Target Price Chart**: Dual line chart showing divergence/convergence between market price and analyst target.
2. **AI Trajectory Meta-Analysis Card**: Synthesis of multi-run developments, sentiment divergence, and catalyst follow-through.
3. **Sentiment & Recommendation Trajectory**: Visual badges and sentiment percentages plotted or listed over time to highlight shifts in sentiment.
4. **Valuation Multiples & Trading Range**: Tracking trailing P/E, forward P/E, and distance from 52-week high/low.
5. **Actionable Insights History Log**: Chronological recap of previous catalysts and risks identified in each report.

## Risks / Trade-offs

- **[Sparse Data for New Tickers]** → If a ticker has only appeared in one pipeline run, time-series line charts have only 1 point, and meta-analysis cannot compare trends.
  - *Mitigation*: The UI will display a single-run point indicator and state: "At least 2 historical pipeline runs are required to generate an AI trajectory meta-analysis. Additional points will appear as daily runs complete."
- **[Timezone Handling]** → Date strings should be formatted consistently in UTC on the backend (`YYYY-MM-DD`).
  - *Mitigation*: Both backend endpoints and frontend date pickers will use `YYYY-MM-DD` strings for deterministic matching.
