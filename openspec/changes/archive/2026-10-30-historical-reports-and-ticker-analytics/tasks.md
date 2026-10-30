## 1. Backend Historical Reports & Analytics APIs

- [x] 1.1 Update `backend/app/models.py` with `TickerTrajectoryAnalysis` model, and `backend/app/llm_schemas.py` with `TrajectoryAnalysis` schema.
- [x] 1.2 Add helper queries in `backend/app/crud.py` to fetch distinct report dates, reports by date, distinct tracked tickers, ticker history, and cached trajectory analyses.
- [x] 1.3 Add trajectory meta-analysis prompt and Pydantic AI agent function in `backend/app/agent.py`.
- [x] 1.4 Implement `GET /api/reports/dates` and `GET /api/reports?date=YYYY-MM-DD` endpoints in `backend/app/main.py`.
- [x] 1.5 Implement `GET /api/analytics/tickers`, `GET /api/analytics/ticker/{ticker}`, and `POST /api/analytics/ticker/{ticker}/meta-analysis` endpoints in `backend/app/main.py`.
- [x] 1.6 Add automated tests in `backend/tests/` verifying the new API endpoints against the SQLite database.

## 2. Frontend Navigation & Historical Reports Explorer

- [x] 2.1 Update shared header navigation across `frontend/src/app/page.tsx` and sub-routes to include Dashboard, Historical Reports, and Ticker Analytics.
- [x] 2.2 Refactor `frontend/src/app/stats/page.tsx` into "Historical Reports" featuring a date selector, run summary metadata, and grid of preview cards for reports on that date.

## 3. Frontend Ticker Analytics Dashboard

- [x] 3.1 Create the `/analytics` page (`frontend/src/app/analytics/page.tsx`) with ticker selector dropdown/tabs populated from `/api/analytics/tickers`.
- [x] 3.2 Implement responsive SVG time-series chart for Current Price vs. Target Price over time with potential upside/downside indicators.
- [x] 3.3 Implement AI Trajectory Meta-Analysis component with on-demand generate/refresh button, cache indicator, and insufficient-data notice.
- [x] 3.4 Implement Recommendation and Community Sentiment trajectory timeline.
- [x] 3.5 Implement Valuation Multiples & Trading Range evolution panel (P/E, forward P/E, 52-week range).
- [x] 3.6 Implement Chronological Actionable Insights and Catalysts log.

## 4. Verification & Documentation

- [x] 4.1 Verify end-to-end functionality between backend APIs and frontend UI for Historical Reports and Ticker Analytics with AI Trajectory Meta-Analysis.
- [x] 4.2 Update project documentation and `README.md` to reflect the new endpoints, capabilities, and frontend views.
