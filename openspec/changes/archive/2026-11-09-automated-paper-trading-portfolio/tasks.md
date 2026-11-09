## 1. Database Layer & Data Models

- [x] 1.1 Define `PortfolioAccount`, `PortfolioPosition`, and `PortfolioSnapshot` SQLAlchemy models in `backend/app/models.py`
- [x] 1.2 Implement CRUD functions in `backend/app/crud.py` for portfolio accounts, open/closed positions, and snapshots
- [x] 1.3 Add database unit tests for portfolio models and CRUD operations in `backend/tests/test_portfolio_crud.py`

## 2. Core Paper Trading Engine

- [x] 2.1 Implement order queue qualification logic from synthesis reports in `backend/app/portfolio_engine.py`
- [x] 2.2 Implement US Market Open execution logic (yfinance market open price fill, position creation, cash deduction)
- [x] 2.3 Implement US Market Close exit evaluation (hard stop -7%, take-profit +15%, archetype time decay, mark-to-market updates)
- [x] 2.4 Implement manual position liquidation function
- [x] 2.5 Implement SPY benchmark alpha calculation and daily snapshot generation
- [x] 2.6 Implement historical bootstrapping simulation utility to backfill past synthesis signals
- [x] 2.7 Add unit tests covering execution, stop-loss, take-profit, time decay, and manual exit rules in `backend/tests/test_portfolio_engine.py`

## 3. Scheduler & API Integration

- [x] 3.1 Register market open and market close scheduled jobs in `backend/app/scheduler.py`
- [x] 3.2 Implement API endpoints in `backend/app/main.py` (`/api/portfolio/summary`, `/api/portfolio/positions`, `/api/portfolio/positions/{id}/close`, `/api/portfolio/journal`, `/api/portfolio/snapshots`, `/api/portfolio/backfill`)
- [x] 3.3 Add API integration tests in `backend/tests/test_portfolio_api.py`

## 4. Frontend Portfolio Dashboard

- [x] 4.1 Update `frontend/src/components/Navbar.tsx` with persistent navigation link to `/portfolio`
- [x] 4.2 Create `/portfolio` page (`frontend/src/app/portfolio/page.tsx`) with portfolio KPI metric summary cards
- [x] 4.3 Create `PortfolioEquityChart.tsx` SVG chart comparing portfolio equity growth vs SPY benchmark
- [x] 4.4 Create `ActivePositionsTable.tsx` displaying open holdings with real-time PnL and manual "Close Position" action
- [x] 4.5 Create `TradeJournalTable.tsx` displaying closed trade ledger with archetype, exit reason, return %, and SPY alpha %

## 5. End-to-End Verification & Documentation

- [x] 5.1 Run full backend test suite (`pytest`) and verify all tests pass
- [x] 5.2 Run frontend production build (`npm run build`) and verify clean compilation
- [x] 5.3 Execute initial historical backfill and verify dashboard data renders properly
- [x] 5.4 Update `README.md` with portfolio architecture, execution schedules, and API endpoints

