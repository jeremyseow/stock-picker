## 1. Database Schema & Data Models

- [x] 1.1 Update `backend/app/models.py` with `CoreEquityIntel`, refactored `RetailReport`, `SmartMoneyReport`, and `SynthesisRecord`.
- [x] 1.2 Update `backend/app/llm_schemas.py` with Pydantic schemas for `CoreEquityIntel` and modular overlays.
- [x] 1.3 Update `backend/app/crud.py` with CRUD functions for `CoreEquityIntel` and date-filtered queries for all three datasets (`retail_reports`, `smart_money_reports`, `synthesis_records`).

## 2. Core Equity Intel Engine & Pipeline Refactoring

- [x] 2.1 Implement `backend/app/core_intel_engine.py` coordinating financial metrics, SEC 10-Q/8-K filings, DuckDuckGo news, and Gemini ground truth synthesis.
- [x] 2.2 Refactor `backend/app/pipeline.py` (Engine 1) to discover retail candidates and attach the Retail Overlay to Core Intel.
- [x] 2.3 Refactor `backend/app/smart_money_pipeline.py` (Engine 2) to attach the Smart Money Inflow Overlay to Core Intel.
- [x] 2.4 Update unified pipeline orchestrators (`run_pipeline.py`, `scheduler.py`, `reset_and_run.py`) to execute Discovery, Core Intel research on unique candidates, Overlays, and Cross-Engine Synthesis.

## 3. Backend API Endpoints

- [x] 3.1 Update `GET /api/reports/dates` to aggregate distinct dates across all three datasets.
- [x] 3.2 Expose `GET /api/smart-money/reports` and `GET /api/synthesis/reports` supporting `?date=YYYY-MM-DD` query filters.
- [x] 3.3 Update `GET /api/reports/{ticker}` to return the Unified Master Report payload (Core Fundamentals, Retail, Smart Money, Synthesis Diagnosis).
- [x] 3.4 Expose `GET /api/analytics/ticker/{ticker}/archetypes` returning chronological archetype progression.

## 4. Frontend Master Report & Tabbed Archives

- [x] 4.1 Update `frontend/src/app/stats/page.tsx` with a 3-tab layout (`Retail Momentum`, `Smart Money & Gov`, `Synthesis Matrix`), badge counts, and graceful empty state fallback.
- [x] 4.2 Upgrade `frontend/src/app/report/[ticker]/page.tsx` to display the Unified Master Report with Core Fundamentals, Retail, Smart Money, and Synthesis sections.
- [x] 4.3 Add Archetype Lifecycle Timeline to `frontend/src/app/analytics/page.tsx`.

## 5. Verification & End-to-End Execution

- [x] 5.1 Add automated tests for Core Intel extraction, candidate deduplication, and historical tab endpoints.
- [x] 5.2 Execute clean database reset and dual-engine pipeline regeneration via `backend/scripts/reset_and_run.py`.
- [x] 5.3 Verify all tests pass, build frontend cleanly, and validate change via `openspec validate modular-core-intel-and-historical-tabs --strict`.

