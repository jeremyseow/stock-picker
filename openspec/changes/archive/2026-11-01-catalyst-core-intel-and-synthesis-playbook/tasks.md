## 1. Backend API Harmonization & Self-Contained Smart Catalyst

- [x] 1.1 Update `get_smart_money_report_detail` in `backend/app/main.py` to fetch and embed `core_intel` (financial metrics, trailing/forward P/E, 52-week range, market cap, ground truth status, SEC filings analysis, events, and risk score).
- [x] 1.2 Implement symmetrical `/api/retail/...` routes in `backend/app/main.py` (`/api/retail/reports`, `/api/retail/today`, `/api/retail/report/{ticker}`) while keeping `/api/reports` as a backward-compatible alias.
- [x] 1.3 Implement symmetrical `/api/master/report/{ticker}` and `/api/synthesis/report/{ticker}` endpoints in `backend/app/main.py` as canonical aliases for `get_ticker_report` (unified master report).

## 2. Frontend Smart Money Detail View Enrichment

- [x] 2.1 Update `frontend/src/app/smart-money/[ticker]/page.tsx` TypeScript interfaces to include embedded `core_intel` fields.
- [x] 2.2 Render the Core Fundamentals & Valuation Metrics grid (Market Cap, P/E, Forward P/E, 52-Week Range, Beta) on the Smart Money report page.
- [x] 2.3 Render the Ground Truth & SEC Filings synthesis panel and Risk Profile scorecard in `/smart-money/[ticker]` so Smart Money reports are self-contained without requiring navigation to retail views.

## 3. High-Alpha Synthesis Master Report & Contrarian Playbook

- [x] 3.1 Create `ContrarianPlaybook.tsx` component in `frontend/src/components/ContrarianPlaybook.tsx` featuring Divergence Heatmap/Scorecard, Tactical Execution Playbook (entry timing, horizon, exit signals), and Archetype Lifecycle Vector.
- [x] 3.2 Update `/report/[ticker]` in `frontend/src/app/report/[ticker]/page.tsx` to integrate the Contrarian Playbook at the top of the Cross-Engine Synthesis section, eliminating redundant duplicate panels.
- [x] 3.3 Harmonize frontend API fetch paths in `frontend/src/app/stats/page.tsx` and `frontend/src/app/report/[ticker]/page.tsx` to use canonical namespaced endpoints (`/api/retail/reports`, `/api/master/report/{ticker}`).

## 4. Verification & Validation

- [x] 4.1 Add automated test cases in `backend/tests/test_api_endpoints.py` testing `/api/retail/reports`, `/api/master/report/{ticker}`, and enriched `/api/smart-money/report/{ticker}`.
- [x] 4.2 Run backend pytest suite and verify all tests pass.
- [x] 4.3 Run `npm run build` in `frontend/` and verify clean build with zero TypeScript errors.
- [x] 4.4 Run `openspec validate catalyst-core-intel-and-synthesis-playbook --strict` and update README.md with the harmonized API endpoints and architecture.
