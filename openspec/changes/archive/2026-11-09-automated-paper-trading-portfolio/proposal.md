## Why

While Antigravity StockPicker generates high-conviction trade ideas across three discovery engines and evaluates forward returns in model calibration, it lacks an automated execution and capital ledger. Users cannot currently see how these signals translate into real portfolio equity, drawdown curves, and dollar PnL under realistic position-sizing and stop-loss constraints.

Introducing an **Automated Paper Trading Portfolio & Trade Journal** closes the loop between discovery and execution. It establishes a simulated \$100,000 fund that automatically acts on top synthesis signals at US market open, enforces strict risk management ($-7\%$ stop-loss, $+15\%$ take-profit, time-decay exits), measures excess alpha against SPY, and maintains a comprehensive trade journal with manual override capabilities.

## What Changes

- **Layer 3 Portfolio Data Model**:
  - Add `portfolio_accounts` table tracking initial capital, cash balance, and total equity.
  - Add `portfolio_positions` table tracking open and closed positions, entry/exit dates and prices, stop-loss and take-profit levels, realized PnL, return percentage, and excess alpha vs SPY.
  - Add `portfolio_snapshots` table capturing daily portfolio equity vs SPY benchmark curves.
- **Automated Order Queue & Market-Open Execution**:
  - Pipeline discovery at 19:00 SGT generates pending trade ideas from `The Rocket` and `Silent Accumulation` archetypes ($Score \ge 75.0$).
  - A scheduled US Market Open job (09:30 ET / 22:30 SGT) executes pending orders at real opening prices via `yfinance`, allocating a fixed \$10,000 (10%) per position up to a strict maximum of 10 concurrent positions.
- **Daily Position & Exit Management Job**:
  - A scheduled US Market Close job (16:00 ET / 05:00 SGT) evaluates active holdings against:
    - Hard Stop-Loss ($-7.0\%$)
    - Take-Profit Target ($+15.0\%$ or fundamental target price)
    - Time-decay exit horizon based on archetype maturation (Rocket = 8 trading days, Silent Accumulation = 22 trading days).
- **Manual Override Controls**:
  - Endpoints and UI buttons allowing the user to trigger an immediate "Close Position Now" on any open holding.
- **Historical Bootstrapping Simulator**:
  - A backfill routine that walks existing historical synthesis runs and price action to generate historical portfolio snapshots and closed trades on Day 1.
- **Frontend Portfolio Dashboard**:
  - New persistent `/portfolio` route featuring KPI metric cards (Total Equity, Realized PnL, Win Rate, Alpha vs SPY), interactive SVG Equity Curve vs SPY, active positions table with manual close buttons, and closed trade journal.

## Capabilities

### New Capabilities
- `paper-trading-portfolio`: Automated position tracking, position sizing (\$100k capital, 10% per slot, max 10 holdings), execution scheduling at US market open, stop-loss ($-7\%$) and take-profit ($+15\%$) exits, time-decay exit horizons, trade journal, and manual position closure.

### Modified Capabilities
- `dashboard-frontend`: Adding `/portfolio` tab to persistent navbar, rendering Equity Curve vs SPY, active positions table with manual close, and closed trade journal.

## Impact

- **Database**: Adds `portfolio_accounts`, `portfolio_positions`, `portfolio_snapshots` tables to `backend/stock_analyzer.db`.
- **Backend Scheduler**: Adds US Market Open (09:30 ET) and Market Close (16:00 ET) scheduled jobs to `backend/app/scheduler.py`.
- **Backend APIs**: Introduces namespaced `/api/portfolio/*` endpoints in `backend/app/main.py`.
- **Frontend**: Adds `frontend/src/app/portfolio/page.tsx` and updates `frontend/src/components/Navbar.tsx`.
- **Dependencies**: Reuses existing `yfinance`, `sqlalchemy`, `apscheduler`, and `pydantic`. Zero external broker or trading SDK dependencies.

