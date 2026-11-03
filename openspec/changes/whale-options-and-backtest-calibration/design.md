## Context

The system currently runs two independent discovery engines (Engine 1 for Retail Reddit momentum and Engine 2 for SEC Form 4 insider cluster purchases & Capitol Hill STOCK Act filings), linking into a shared, 6-hour cached `core_equity_intels` table and evaluated via a Cross-Engine Synthesis Hub.

To capture immediate 1-to-4 week institutional flow and validate all heuristic formulas empirically, this change adds:
1. **Engine 3 (Institutional Whale Options Radar)**: Detecting high-conviction unusual options activity.
2. **Backtesting & Model Calibration Engine**: Tracking $T+5, T+15, T+30$ forward returns relative to SPY and tuning scoring weights across all engines.

See `proposal.md` and capability specs for background motivation and behavioral requirements.

## Goals / Non-Goals

**Goals:**
- Provide zero-cost options chain ingestion and unusual volume-to-open-interest scanning via `yfinance`.
- Persist Engine 3 options data in decoupled `options_whale_tickers` and `options_whale_reports` tables linked to `core_equity_intels`.
- Integrate Engine 3 options pipeline directly into the daily APScheduler job (`app/scheduler.py`) and the CLI runner (`run_pipeline.py`) prior to Triangulation Synthesis.
- Integrate options flow into `synthesis_engine.py` to upgrade the 2-way synthesis matrix into a 3-way Triangulation Matrix.
- Implement an automated walk-forward backtest calculator calculating excess alpha over the SPY benchmark at $T+5, T+15, T+30$ trading days for historical picks.
- Provide a centralized dynamic weights registry (`app/scoring_weights.py`) that engines reference, enabling production calibration without code changes.
- Build a responsive Next.js `/calibration` dashboard displaying the performance scorecard and active vs. recommended weights with an "Apply Recommended Weights" button.

**Non-Goals:**
- Sub-millisecond tick-by-tick OPRA options order flow or paid third-party vendor subscriptions ($100+/month).
- Live broker order placement or real-money execution.

## Decisions

### 1. Zero-Cost Options Chain Scanning via `yfinance`
- **Choice**: Use `yfinance.Ticker.options` and `.option_chain()` to inspect call and put strikes for candidate equities.
- **Rationale**: `yfinance` provides full public strike data, bid/ask spreads, volume, open interest (OI), and implied volatility with no API key or subscription fees.
- **Alternative considered**: Third-party APIs (Unusual Whales, FlowAlgo, Polygon Options). Rejected due to high recurring monthly fees ($50–$150/mo) and vendor lock-in.

### 2. Decoupled Engine 3 Database Models
- **Choice**: Add `OptionsWhaleTicker` and `OptionsWhaleReport` with a foreign key to `core_equity_intels`, mirroring the pattern of `RetailReport` and `SmartMoneyReport`.
- **Rationale**: Preserves architectural modularity and isolation. Existing tables remain untouched except for 3 nullable columns in `synthesis_records` (`whale_options_flow`, `whale_options_score`, `put_call_ratio`).
- **Alternative considered**: Storing options metrics inside `raw_metrics` JSON blob in `core_equity_intels`. Rejected because typed SQL columns allow date-based historical querying and indexing.

### 3. Dynamic Weights Registry (`app/scoring_weights.py`)
- **Choice**: Manage all scoring weights in a centralized configuration module with SQLite/JSON persistence for approved overrides.
  - Engine 1: Post vs. comment engagement multipliers, minimum mention floor.
  - Engine 2: Role weights (C-suite, Directors), cluster multipliers, dollar volume cap, committee jurisdiction multiplier.
  - Engine 3: Unusual volume-to-OI cutoff (e.g. 2.5x), minimum premium threshold, OTM call delta range.
  - Synthesis: Timing edge decay factor, archetype boundary thresholds.
- **Rationale**: Engines dynamically reference active weights, allowing one-click calibration from the frontend without redeploying code.

### 4. Walk-Forward Alpha Computation & Benchmark Alignment
- **Choice**: Compute returns on close-to-close prices:
  $$\text{Alpha}_{T+k} = \left(\frac{\text{Price}_{T+k} - \text{Price}_{T_0}}{\text{Price}_{T_0}}\right) - \left(\frac{\text{SPY}_{T+k} - \text{SPY}_{T_0}}{\text{SPY}_{T_0}}\right)$$
  Cache calculated returns in SQLite (`model_backtest_runs`) to prevent repetitive external Yahoo Finance queries on every dashboard load.
- **Rationale**: Standardized benchmark comparison prevents bull-market bias and isolates true stock-picking edge.

## Risks / Trade-offs

- **[Risk] `yfinance` Options Chain Rate Limiting**: Fetching full option chains across 50+ tickers could trigger Yahoo Finance rate limiting.  
  → *Mitigation*: Limit option chain scans to the top 10 discovery candidates from Engine 1, Engine 2, and active tracked watchlists, with 2-second rate-limiting intervals.
- **[Risk] Small Historical Sample Size on New Deployments**: Fresh databases have few historical pipeline runs, leading to sparse $T+30$ data.  
  → *Mitigation*: The backtester gracefully checks available horizons and displays sample count warnings (e.g. "Preliminary (N < 20 runs)") until enough longitudinal runs accumulate.
- **[Risk] Overfitting / Curve-Fitting During Calibration**: Optimizing weights exclusively on past runs can overfit noise.  
  → *Mitigation*: Enforce conservative bounds on all parameter sweeps (e.g. CEO weight constrained to [2.0, 4.5], cluster multiplier constrained to [1.5, 3.5]) to maintain fundamental grounding.

