## Purpose

Calculates empirical walk-forward forward returns against the S&P 500 benchmark for historical recommendations and archetypes, generating performance scorecards and calibrated scoring weights across all discovery engines.

## ADDED Requirements

### Requirement: Walk-Forward Return Calculation and Performance Scorecard
The system SHALL compute historical forward returns at T+5, T+15, and T+30 trading day horizons for all recorded discovery engine picks relative to the SPY benchmark.

#### Scenario: Walk-Forward Alpha Computation
- **WHEN** the backtesting evaluation executes
- **THEN** the system queries historical closing prices from market data feeds for each discovery date and calculates the percentage return and excess alpha over SPY at T+5, T+15, and T+30 days.

#### Scenario: Generate Multi-Engine Scorecard
- **WHEN** backtest returns are compiled
- **THEN** the system computes win rate (% with positive alpha vs. SPY), average excess return, and maximum drawdown segmented by market archetype (The Rocket, Silent Accumulation, The Retail Trap, Market Noise) and recommendation rating (BUY, HOLD, SELL).

### Requirement: Parameter Weight Calibration
The system SHALL evaluate scoring parameters across Engine 1, Engine 2, Engine 3, and Cross-Engine Synthesis to calculate recommended parameter weights that maximize historical risk-adjusted return (Sharpe ratio and alpha).

#### Scenario: Calculate Tuned Hyperparameters
- **WHEN** model calibration runs
- **THEN** the system runs an empirical parameter sweep over historical discovery records and outputs recommended weights for role seniority, cluster multipliers, volume caps, committee multipliers, retail engagement, and options flow thresholds alongside projected alpha improvement.

### Requirement: Serve Calibration Scorecards and Persist Approved Weights
The system SHALL provide API endpoints to inspect performance scorecards, active weights, recommended weights, and apply approved calibrations into production configuration.

#### Scenario: Query Calibration Scorecard and Weights
- **WHEN** a client requests `/api/calibration/scorecard`
- **THEN** the system returns overall win rates, performance metrics by archetype, active parameter weights, and recommended calibrated weights with their expected alpha impact.

#### Scenario: Apply Recommended Weights
- **WHEN** a client submits a POST request to `/api/calibration/apply-weights`
- **THEN** the system persists the approved calibrated weights into production configuration, timestamps the calibration event, and makes subsequent pipeline runs use the updated weights.

