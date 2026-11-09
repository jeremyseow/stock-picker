## Purpose

Ingests, filters, and scores equity options market activity to detect institutional whale accumulation through unusual volume-to-open-interest spikes, aggressive out-of-the-money call sweeps, and put/call volume skews.

## ADDED Requirements

### Requirement: Ingest Option Chains and Detect Unusual Options Activity
The system SHALL ingest full options chains for tracked equities and screen for unusual trading spikes where daily trading volume significantly exceeds open interest.

#### Scenario: Unusual Volume Over Open Interest Detection
- **WHEN** the daily options scanning job executes
- **THEN** the system evaluates call and put contracts across available expiration dates and flags contracts where daily traded volume exceeds 2.5x open interest and total traded dollar premium exceeds $100,000.

#### Scenario: Aggressive Out-Of-The-Money Call Sweep Identification
- **WHEN** contracts exhibit unusual volume
- **THEN** the system identifies strikes situated 5% to 30% above the current stock price expiring within 14 to 45 calendar days, classifying them as short-horizon institutional whale sweeps.

### Requirement: Score Institutional Whale Conviction
The system SHALL calculate an aggregated Whale Conviction Score (0.0 to 100.0) for candidate tickers based on unusual volume multipliers, net bullish call premium, and put/call volume ratio.

#### Scenario: Whale Conviction Score Calculation
- **WHEN** candidate tickers exhibit flagged options flow
- **THEN** the system computes a composite score weighting total bullish call premium, the peak volume-to-OI ratio, and the inverse put/call ratio, ranking the top 5 highest-conviction whale candidates.

### Requirement: Serve Whale Options Data via Namespaced APIs
The system SHALL provide canonical REST API endpoints delivering the latest whale candidates and detailed ticker options flow reports.

#### Scenario: Query Latest Whale Options Tickers
- **WHEN** a client requests `/api/options/today`
- **THEN** the system returns the top-ranked whale options tickers with conviction scores, top unusual strikes, and put/call ratios.

#### Scenario: Query Individual Whale Options Report
- **WHEN** a client requests `/api/options/report/{ticker}`
- **THEN** the system returns the detailed options ledger including flagged strikes, expiration dates, open interest ratios, estimated premium, and linked core equity intelligence.

### Requirement: Pipeline and Scheduler Integration
The system SHALL execute Engine 3 options flow scanning as an automated step in both the scheduled daily cron runner and the manual CLI execution script.

#### Scenario: Scheduled Execution
- **WHEN** the daily 19:00 SGT scheduler triggers the pipeline
- **THEN** the system runs Engine 3 options scanning sequentially after Engine 1 and Engine 2 before executing cross-engine synthesis.

#### Scenario: CLI Execution
- **WHEN** an operator runs `backend/run_pipeline.py`
- **THEN** Engine 3 options scanning executes as an explicit pipeline step, logging progress and saving options records alongside retail and smart money reports.

