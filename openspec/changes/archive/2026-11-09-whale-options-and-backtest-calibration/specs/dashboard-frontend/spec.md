## ADDED Requirements

### Requirement: Display Model Calibration and Backtest Scorecard
The frontend dashboard SHALL provide a dedicated Model Calibration page (`/calibration`) displaying historical backtest win rates against the S&P 500, performance breakdowns by archetype, active scoring weights, and recommended tuned weights.

#### Scenario: View Calibration Scorecard
- **WHEN** the user navigates to `/calibration`
- **THEN** the view displays:
  - Top summary metrics: Overall Hit Rate at T+30, Average Alpha vs. SPY, Maximum Drawdown, and Sample Run Count.
  - Archetype Performance Table: Average forward return, win rate, and risk metrics for The Rocket, Silent Accumulation, The Retail Trap, and Market Noise.
  - Weights Comparison Table: Current production weights vs. recommended calibrated weights across Engine 1, Engine 2, Engine 3, and Cross-Engine Synthesis with projected alpha impact.

#### Scenario: Apply Recommended Calibrated Weights
- **WHEN** the user clicks the "Apply Recommended Weights" button on `/calibration`
- **THEN** the frontend triggers a POST to `/api/calibration/apply-weights`, updates the active weights display, and renders a confirmation notification with the calibration timestamp.

### Requirement: Display Whale Options Flow Radar
The frontend dashboard SHALL provide views for Engine 3 Whale Options flow, including a dedicated tab in Historical Reports (`/stats`) and an Options Radar card on individual report pages.

#### Scenario: View Options Whale Tab in Historical Reports
- **WHEN** the user navigates to `/stats` and selects a historical date
- **THEN** the tab bar displays a fourth tab `Whale Options (N)` displaying cards for all options flow picks recorded on that date.

#### Scenario: View Whale Options Overlay on Stock Report
- **WHEN** the user views a detailed stock report (`/report/[ticker]`)
- **THEN** an Options Flow Radar card renders the put/call ratio, unusual volume-to-open-interest ratio, and top institutional call sweeps with expiration dates and strike prices.

