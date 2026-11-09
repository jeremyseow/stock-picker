## 1. Database Models & Centralized Weights Registry

- [x] 1.1 Add `OptionsWhaleTicker` and `OptionsWhaleReport` models in `backend/app/models.py` with foreign key linking to `core_equity_intels`.
- [x] 1.2 Add nullable whale options flow columns (`whale_options_flow`, `whale_options_score`, `put_call_ratio`) to `SynthesisRecord`.
- [x] 1.3 Add `ModelCalibrationRun` model to store historical backtest scorecards and timestamped weight calibrations.
- [x] 1.4 Create `backend/app/scoring_weights.py` centralized weights registry for Engine 1, Engine 2, Engine 3, and Cross-Engine Synthesis with persistence.

## 2. Engine 3 (Whale Options Radar) Ingestion & Scoring

- [x] 2.1 Implement `backend/app/options_scraper.py` using `yfinance` to fetch option chains, filter unusual Volume > 2.5x OI, and identify OTM call sweeps.
- [x] 2.2 Implement `backend/app/options_scorer.py` to calculate the 0-100 Whale Conviction Score based on unusual OI multipliers, net bullish premium, and put/call ratio.
- [x] 2.3 Implement `backend/app/options_pipeline.py` orchestrating Engine 3 options scanning and linking with `CoreEquityIntel`.
- [x] 2.4 Add async CRUD queries in `backend/app/crud.py` for whale options tickers, reports, and historical dates.
- [x] 2.5 Integrate Engine 3 (`run_options_pipeline`) into the scheduled background job (`backend/app/scheduler.py`) and CLI orchestration runner (`backend/run_pipeline.py`).

## 3. Triangulation Synthesis Matrix Expansion

- [x] 3.1 Update `backend/app/synthesis_engine.py` to ingest Engine 3 options flow alongside Engine 1 (Retail) and Engine 2 (Smart Money).
- [x] 3.2 Add the 3-way Triangulation Matrix logic elevating "Silent Accumulation (Whale Front-Run)" with max timing edge when call sweeps align with insider buys.

## 4. Walk-Forward Backtesting & Calibration Engine

- [x] 4.1 Implement `backend/app/backtest_engine.py` to compute historical forward returns at T+5, T+15, and T+30 trading days relative to the SPY benchmark.
- [x] 4.2 Implement performance scorecard compilation (win rate, average alpha vs. SPY, maximum drawdown by archetype and recommendation).
- [x] 4.3 Implement parameter calibration optimizer calculating recommended weights for Engines 1, 2, 3, and Synthesis that maximize risk-adjusted alpha.

## 5. Backend REST API Endpoints & Integration Tests

- [x] 5.1 Add canonical options endpoints (`/api/options/today`, `/api/options/reports`, `/api/options/report/{ticker}`) in `backend/app/main.py`.
- [x] 5.2 Add calibration endpoints (`/api/calibration/scorecard` and `/api/calibration/apply-weights`) in `backend/app/main.py`.
- [x] 5.3 Write unit and integration tests in `backend/tests/test_options_and_calibration.py` covering options scoring, backtest alpha math, and weight persistence.

## 6. Frontend Calibration & Options Views

- [x] 6.1 Create `/calibration` page displaying the Backtest Scorecard, Archetype Breakdown, Active vs. Recommended Weights table, and "Apply Recommended Weights" button.
- [x] 6.2 Add "Model Calibration" navigation link in `frontend/src/components/Navbar.tsx`.
- [x] 6.3 Update Historical Reports (`frontend/src/app/stats/page.tsx`) with a 4th tab `Whale Options (N)`.
- [x] 6.4 Create `OptionsFlowCard.tsx` component and embed it on the Unified Master Report (`frontend/src/app/report/[ticker]/page.tsx`).
- [x] 6.5 Run full backend test suite (`pytest`) and frontend production build (`npm run build`) to verify clean compilation.

