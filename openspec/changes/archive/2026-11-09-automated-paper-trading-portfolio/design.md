## Context

The Antigravity StockPicker system produces high-conviction trade ideas through its three discovery engines and synthesizes them into market archetypes (`The Rocket`, `Silent Accumulation`, `The Retail Trap`, `Market Noise`) with composite conviction scores (0–100). The model calibration subsystem tracks 1-day, 5-day, and 20-day forward price returns across archetypes, but lacks a capital management layer. Without a simulated portfolio, users cannot observe realized dollar PnL, equity drawdowns, capital utilization, or active excess returns against the S&P 500 under realistic execution constraints.

This design introduces a decoupled paper trading execution engine, an institutional ledger data model, scheduled market-synchronized jobs, and an interactive frontend dashboard at `/portfolio`.

See `proposal.md` for motivation and background.

## Goals / Non-Goals

**Goals:**
- Provide a persistent 3-table SQLite ledger (`portfolio_accounts`, `portfolio_positions`, `portfolio_snapshots`) with zero impact on existing tables.
- Schedule discrete, realistic US Market Open (09:30 ET / 22:30 SGT) order fills and US Market Close (16:00 ET / 05:00 SGT) exit evaluations via APScheduler.
- Enforce strict portfolio constraints: \$100,000 initial capital, \$10,000 (10%) per trade, maximum 10 concurrent positions, and strict queue discipline (skip new candidates when fully invested).
- Execute rule-based exits: $-7.0\%$ hard stop-loss, $+15.0\%$ take-profit target, and archetype maturation time limits (8 days for `The Rocket`, 22 days for `Silent Accumulation`).
- Support manual user liquidation via UI and API endpoint.
- Benchmark position and portfolio equity growth against `SPY` (S&P 500) to measure cumulative alpha.
- Provide a historical backfill bootstrap utility to immediately populate past performance from existing synthesis records.
- Deliver an interactive Next.js dashboard route (`/portfolio`) with KPI cards, an SVG equity curve vs SPY, active positions management, and a trade journal.

**Non-Goals:**
- Live broker integration or automated real-money trading.
- Intraday tick-by-tick order fills or trailing stop logic (evaluation occurs on daily bar open/close).
- Short selling or option contract simulation (long-only equity positions).
- Fractional share allocation (positions are integer share counts floored to \$10,000).

## Decisions

### 1. Decoupled Market-Synchronized Scheduler vs Pipeline-Coupled Execution
- **Decision**: Execute orders at US Market Open (09:30 ET / 22:30 SGT) and evaluate exits at US Market Close (16:00 ET / 05:00 SGT) via dedicated APScheduler jobs, separate from the 19:00 SGT discovery pipeline.
- **Rationale**: The synthesis pipeline runs pre-market (19:00 SGT / 07:00 ET). Filling orders at 19:00 SGT would unrealistically execute at yesterday's close price. Generating queued candidates pre-market and filling them at 09:30 ET captures actual opening gap prices via `yfinance`. Similarly, evaluating stops and time-decay at market close prevents premature intraday liquidations.
- **Alternatives Considered**: Executing immediately during the synthesis run at 19:00 SGT was rejected because it causes unrealistic pricing slippage and ignores overnight news and opening gap effects.

### 2. Standard Fixed Position Sizing with Strict Queue Discipline
- **Decision**: Fixed \$10,000 per position (10% of \$100,000 capital) with a hard cap of 10 concurrent positions. When all 10 slots are filled, newly surfaced synthesis signals are skipped.
- **Rationale**: Simple, transparent, and prevents capital over-concentration or curve-fitting. Queue discipline Option A avoids forced early liquidations of winning or consolidating trades to make room for newer signals.
- **Alternatives Considered**: Dynamic Kelly sizing or volatility parity was rejected as premature optimization prior to establishing sufficient trade volume.

### 3. Quant Priors Evolving to Bayesian Calibration Synergy
- **Decision**: Initialize maturation holding horizons with domain priors (8 trading days for `The Rocket` momentum bursts, 22 trading days for `Silent Accumulation` institutional base building). As model calibration cohorts accumulate ($N \ge 15$ closed trades per archetype), holding horizons transition via Bayesian shrinkage toward empirical peak-return durations.
- **Rationale**: Solves the cold-start problem gracefully without leaving trades open indefinitely, while establishing a direct mathematical feedback loop between model calibration and paper trade execution.
- **Alternatives Considered**: Static holding periods without model calibration feedback were rejected because they fail to leverage the platform's empirical diagnostic capabilities.

### 4. S&P 500 (SPY) Relative Alpha Benchmarking
- **Decision**: Fetch SPY benchmark prices on the exact entry and exit dates of each trade, computing active excess alpha (`position_return_pct - spy_return_pct`). Calculate daily portfolio snapshot returns against SPY baseline.
- **Rationale**: Absolute returns can be deceptive during broad market bull runs or corrections. Measuring excess return against the market benchmark shows whether synthesis-driven selection generates real alpha.

### 5. Architectural Data Model
- **`portfolio_accounts`**:
  - `id` (INTEGER PK)
  - `name` (TEXT, default 'Primary Fund')
  - `initial_balance` (REAL, default 100000.0)
  - `cash_balance` (REAL, default 100000.0)
  - `total_equity` (REAL, default 100000.0)
  - `created_at`, `updated_at` (DATETIME)
- **`portfolio_positions`**:
  - `id` (INTEGER PK)
  - `account_id` (INTEGER FK)
  - `ticker` (TEXT)
  - `archetype` (TEXT)
  - `conviction_score` (REAL)
  - `status` (TEXT: `OPEN`, `CLOSED`)
  - `shares` (INTEGER)
  - `entry_date` (DATETIME)
  - `entry_price` (REAL)
  - `target_price` (REAL, nullable)
  - `stop_loss_price` (REAL)
  - `exit_date` (DATETIME, nullable)
  - `exit_price` (REAL, nullable)
  - `exit_reason` (TEXT, nullable: `STOP_LOSS`, `TAKE_PROFIT`, `TIME_EXIT`, `MANUAL`)
  - `realized_pnl` (REAL, nullable)
  - `return_pct` (REAL, nullable)
  - `holding_days` (INTEGER, default 0)
  - `spy_entry_price` (REAL, nullable)
  - `spy_exit_price` (REAL, nullable)
  - `spy_return_pct` (REAL, nullable)
  - `excess_alpha_pct` (REAL, nullable)
  - `created_at`, `updated_at` (DATETIME)
- **`portfolio_snapshots`**:
  - `id` (INTEGER PK)
  - `account_id` (INTEGER FK)
  - `snapshot_date` (DATETIME)
  - `cash_balance` (REAL)
  - `invested_capital` (REAL)
  - `total_equity` (REAL)
  - `portfolio_return_pct` (REAL)
  - `spy_price` (REAL)
  - `spy_return_pct` (REAL)
  - `excess_alpha_pct` (REAL)
  - `open_positions_count` (INTEGER)
  - `created_at` (DATETIME)

## Risks / Trade-offs

- **[Risk]** Market holiday and weekend price staleness when querying `yfinance`.
  - **Mitigation**: The execution and exit evaluation services verify market calendar trading days before running fills, skipping weekends and NYSE holidays.
- **[Risk]** yfinance rate limiting during historical bootstrapping.
  - **Mitigation**: Backfill queries batch ticker histories over the relevant historical window in a single `yf.download` call rather than repeated per-day queries.
- **[Risk]** State synchronization between concurrent user manual exits and scheduled jobs.
  - **Mitigation**: Use atomic database transactions with SQLite `with db.begin():` or row verification (`WHERE status = 'OPEN'`) to ensure a position cannot be double-closed.

## Migration Plan

1. **Database Schema Addition**: Add new SQLAlchemy models to `backend/app/models.py`. Tables are automatically created at backend startup via `Base.metadata.create_all(bind=engine)`. No migrations or drops required.
2. **Backend Service & Routing**: Implement `portfolio_engine.py` and register `/api/portfolio/*` routes in `main.py`.
3. **Scheduler Integration**: Register market open and market close jobs in `backend/app/scheduler.py`.
4. **Bootstrapping**: Provide a one-click or automated bootstrap script to populate historical trades and snapshots from existing synthesis history.
5. **Frontend View**: Create `frontend/src/app/portfolio/page.tsx`, add the Portfolio link to `Navbar.tsx`, and verify full frontend build (`npm run build`).

