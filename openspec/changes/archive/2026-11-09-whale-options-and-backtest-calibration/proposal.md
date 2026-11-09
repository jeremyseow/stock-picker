## Why

The current system relies on heuristic, fixed weights for scoring retail buzz (Engine 1) and smart money insider convictions (Engine 2) without empirical feedback on actual market performance. Furthermore, while corporate insiders (Form 4) operate on long 3-to-12 month horizons and retail traders operate reactively after rallies begin, the platform lacks visibility into institutional hedge fund positioning—who express immediate 1-to-4 week conviction through aggressive out-of-the-money options sweeps and dark pool accumulation. 

Introducing Engine 3 (Institutional Whale Options Flow) and an empirical Walk-Forward Backtesting & Model Calibration Suite closes both gaps: it captures short-term whale conviction and evaluates historical forward returns ($T+5, T+15, T+30$) against the S&P 500 benchmark, surfacing performance scorecards and mathematically recommended weights across all three engines.

## What Changes

- **Engine 3 (Institutional Whale Options Radar)**:
  - Scrapes zero-cost options chain data via `yfinance` to detect unusual options activity (Volume > $2.5\times$ Open Interest, out-of-the-money call sweeps, and put/call volume skews).
  - Calculates a normalized Whale Conviction Score based on unusual open interest multipliers, net bullish call premium, and expiration proximity.
  - Stores records in a decoupled `options_whale_reports` table linked to `core_equity_intels`.
- **Triangulation Matrix Expansion (Cross-Engine Synthesis)**:
  - Extends the 2-way synthesis engine into a 3-way Triangulation Matrix, incorporating Whale Options flow into archetype diagnosis (e.g. elevating *Silent Accumulation* into high-conviction *Stealth Whales* when institutional call sweeps align with C-suite Form 4 buys).
- **Walk-Forward Historical Backtesting Engine**:
  - Calculates forward market returns at $T+5$, $T+15$, and $T+30$ trading days relative to the SPY benchmark for every recorded ticker recommendation and synthesis archetype.
  - Generates an empirical Performance Scorecard tracking win rates, average alpha, and maximum drawdowns.
  - Evaluates parameter weights across Engine 1, Engine 2, Engine 3, and Synthesis, computing recommended tuned weights that maximize the Sharpe ratio / alpha.
- **Calibration & Backtest Dashboard (`/calibration`)**:
  - Displays a clean visual Scorecard detailing overall hit rate vs. SPY and performance broken down by market archetype (*The Rocket*, *Silent Accumulation*, *The Retail Trap*, *Market Noise*).
  - Presents a structured side-by-side comparison table of Current Active Weights vs. Recommended Tuned Weights across all engines.
  - Provides a single-click action to persist recommended calibrated weights into active production configuration.
- **Frontend Whale Flow Overlays**:
  - Integrates an Options Flow Radar card into individual stock detail reports and adds an "Options Whale Flow" tab in the Historical Reports explorer.

## Capabilities

### New Capabilities
- `whale-options-radar`: Ingests and scores unusual options market activity, volume-to-open-interest spikes, and put/call volume skews as Engine 3.
- `model-backtest-calibration`: Computes historical forward returns ($T+5, T+15, T+30$ vs. S&P 500 benchmark), performance scorecards by archetype and recommendation, and empirical weight calibration across all engines.

### Modified Capabilities
- `cross-engine-synthesis`: Integrates Engine 3 Whale Options flow into the archetype classification and contrarian playbook logic to form a 3-way Triangulation Matrix.
- `dashboard-frontend`: Adds the `/calibration` page (Backtest Scorecard & Weight Calibration), an Options Whale tab in `/stats`, and options radar cards across detail reports.

## Impact

- **Backend Models & Database**: Introduces new tables `options_whale_tickers`, `options_whale_reports`, and `model_calibration_runs` linked to `core_equity_intels`. Adds optional nullable columns to `synthesis_records` for options flow signals.
- **Scoring & Engine Pipelines**: Adds `app/options_pipeline.py` and `app/backtest_engine.py`. Adds configurable calibration parameters dictionary in `app/config.py` (or JSON config) that engines reference dynamically.
- **Frontend Routes & Components**: Adds new route `/calibration`, updates `/stats` (historical options tab), and adds `OptionsFlowCard` to report detail pages.
- **APIs**: Exposes `/api/options/...` namespaced endpoints, `/api/calibration/scorecard`, and `/api/calibration/apply-weights`.

