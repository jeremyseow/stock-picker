# dashboard-frontend Specification

## Purpose
Provides a responsive Next.js web application for browsing daily trending stock picks, exploring detailed four-pillar equity research reports, viewing historical run archives, and inspecting longitudinal ticker trajectories alongside Smart Money insider trading radars.

## Requirements

### Requirement: Shared Navigation Header
The frontend dashboard and all sub-routes SHALL feature a persistent, styled navigation header bar to switch between the main Dashboard (Retail Momentum), Smart Money & Gov, Cross-Engine Synthesis Matrix, Historical Reports, Ticker Analytics, and Paper Trading Portfolio.

#### Scenario: Navigate Pages
- **WHEN** a user clicks on "Retail Momentum", "Smart Money & Gov", "Synthesis Matrix", "Historical Reports", "Ticker Analytics", or "Portfolio" links in the header
- **THEN** the router navigates the user to the corresponding page.

### Requirement: Display Rich Daily Top Stocks List
The frontend dashboard homepage SHALL display the top highly discussed stocks from the most recent pipeline run as rich preview cards. The backend `/api/tickers/today` endpoint SHALL return the tickers of the latest run (all `DailyTicker` rows within 1 hour of the newest timestamp) rather than filtering by calendar day, so the dashboard is never empty between runs.

#### Scenario: View Daily Stocks
- **WHEN** a user navigates to the dashboard homepage
- **THEN** they see card previews showing:
  - Ticker symbol and rank.
  - An AI recommendation badge (BUY, HOLD, SELL, or NO REPORT) with color indicator.
  - Sector and Industry.
  - Live stock price and target price (if report exists).
  - Reddit mention count and engagement score.

#### Scenario: View Run Date
- **WHEN** the dashboard displays tickers
- **THEN** a badge below the page subtitle shows "Picks from run on {date, time}", converting the backend's naive UTC timestamp to the user's local timezone.

#### Scenario: Stale Run Warning
- **WHEN** the latest run is 1 or more days old
- **THEN** the run-date badge is styled amber and shows "(N days ago)"; otherwise it is styled green.

### Requirement: Display Individual Stock Report
The frontend dashboard SHALL allow the user to click on a stock ticker to view its detailed unified master equity research report, dynamically presenting Core Fundamentals, Retail Momentum sentiment, Smart Money inflow catalysts, and Cross-Engine synthesis diagnosis with a Divergence Scorecard and Contrarian Execution Playbook.

#### Scenario: View Report Details
- **WHEN** a user clicks on a stock ticker from any list, feed, or matrix
- **THEN** a detailed unified view opens, displaying:
  - **Master Hero Header**: Ticker symbol, company name, sector/industry, current price vs target price, calculated potential upside percentage, and active signal badges (Retail recommendation and/or Smart Money conviction tier).
  - **Cross-Engine Divergence & Contrarian Playbook**:
    1. **Divergence Heatmap**: Comparative bar or visual meter comparing Retail Sentiment vs Smart Money Conviction.
    2. **Contrarian Execution Playbook**: Concrete tactical gameplan with Entry Timing, Target Horizon, and Exit Signals based on the market archetype.
    3. **Lifecycle Phase Vector**: Step indicator displaying where the ticker sits in its lifecycle (`Silent Accumulation ➔ The Rocket ➔ The Retail Trap ➔ Market Noise`).
  - **Core Fundamentals & Ground Truth Grid**:
    1. **Financial Ratios Grid**: Trailing P/E, forward P/E, 52-week trading range, market cap.
    2. **Ground Truth**: Corporate Position and SEC Filings/News Analysis.
    3. **Events & Happenings**: Key corporate events, product launches, or macro/geopolitical events.
    4. **Risk Assessment**: Risk level badge (Low/Medium/High) and risk factors.
  - **Smart Money & Political Inflow Section**: Inflow ledger table, cluster buying metrics, committee relevance tags, catalyst horizon, and swing thesis.
  - **Retail Momentum Section**: Sentiment meter, narrative hype summary, and community expectations.

### Requirement: Display Date-Selected Historical Reports
The frontend dashboard SHALL provide a Historical Reports view that enables users to view all available pipeline run dates and display intelligence reports across three dedicated tabs: Retail Momentum, Smart Money & Gov, and Synthesis Matrix.

#### Scenario: View Available Dates
- **WHEN** the user navigates to the Historical Reports view
- **THEN** the interface fetches and presents a list or picker of all historical run dates aggregated across all engines.

#### Scenario: Select Date and View Reports
- **WHEN** the user selects a specific date
- **THEN** the dashboard renders three tabs with item count badges (`Retail Momentum (N)`, `Smart Money & Gov (N)`, `Synthesis Matrix (N)`) and displays the corresponding reports for the active tab.

#### Scenario: Engine Not Tracked on Historical Date
- **WHEN** the user selects a tab for an engine that was not recorded on the selected date
- **THEN** a clean informative empty state card indicates that the engine was not tracked on that date.

#### Scenario: No Reports for Date
- **WHEN** the user selects a date that has no recorded reports across any engine
- **THEN** a clear informative message is displayed stating no reports are available for that date.

### Requirement: Display Smart Money & Political Scout View
The frontend dashboard SHALL provide a dedicated Smart Money view (`/smart-money`) displaying Engine 2 picks and individual catalyst reports (`/smart-money/[ticker]`) self-contained with Core Fundamentals and SEC ground truth.

#### Scenario: View Smart Money Feed
- **WHEN** the user navigates to `/smart-money`
- **THEN** they see ranked cards displaying high-conviction insider cluster buys, Congressional trades, committee relevance tags, dollar volumes, and catalyst time horizons.

#### Scenario: View Smart Money Individual Report
- **WHEN** the user opens `/smart-money/[ticker]`
- **THEN** they see a self-contained report displaying:
  1. The Inflow Ledger detailing executive and political transactions, cluster metrics, committee jurisdictions, and a medium-term swing thesis.
  2. The Core Fundamentals & Ground Truth Grid (valuation multiples, SEC 10-Q/8-K ground truth, corporate positioning, key catalyst events, and risk scores).

### Requirement: Display Cross-Engine Synthesis Matrix
The frontend dashboard SHALL provide a Synthesis Matrix view (`/synthesis`) displaying market archetype diagnoses and retail awareness measurements.

#### Scenario: View Synthesis Matrix
- **WHEN** the user navigates to `/synthesis`
- **THEN** they see active stocks mapped across the 4 archetypes (The Rocket, The Retail Trap, Silent Accumulation, Market Noise) with retail awareness indicators and actionable divergence callouts.

### Requirement: Display Archetype Lifecycle Trajectory in Ticker Analytics
The frontend Ticker Analytics view SHALL display an Archetype Lifecycle Timeline showing how a stock migrated across synthesis archetypes over historical pipeline runs.

#### Scenario: View Archetype Trajectory
- **WHEN** viewing a ticker with historical pipeline reports
- **THEN** an Archetype Progression timeline illustrates the stock's transition between archetypes (e.g. Silent Accumulation to The Rocket to The Retail Trap) with corresponding timing edge scores.

### Requirement: Standardized API Namespacing and Unified Link Terminology
The application SHALL provide consistently namespaced endpoints and unified link labels across all user interfaces.

#### Scenario: Query Namespaced Endpoints
- **WHEN** a client requests data for Retail Momentum, Smart Money Scout, Cross-Engine Synthesis, or Master Reports
- **THEN** the backend serves consistently namespaced paths:
  - `/api/retail/reports`, `/api/retail/tickers/today`, and `/api/retail/report/{ticker}` (Engine 1)
  - `/api/smart-money/reports` and `/api/smart-money/report/{ticker}` (Engine 2)
  - `/api/synthesis/reports` and `/api/synthesis/latest` (Cross-Engine)
  - `/api/master/report/{ticker}` (Unified Master Report)

### Requirement: Display Paper Trading Portfolio Dashboard
The frontend SHALL provide a dedicated Paper Trading Portfolio page at `/portfolio` featuring portfolio KPI summary cards, an interactive equity performance curve benchmarked against SPY, an active positions table with manual close actions, and a closed trade journal.

#### Scenario: View Portfolio KPI Summary Cards
- **WHEN** a user navigates to `/portfolio`
- **THEN** the page displays summary metric cards including:
  - Total Portfolio Equity and Total Return ($ and %)
  - Available Cash Balance vs Invested Capital
  - Win Rate (% profitable closed trades)
  - Cumulative Excess Alpha vs SPY benchmark
  - Active Holdings count (e.g. `4 / 10 slots filled`)

#### Scenario: View Interactive Equity Curve vs SPY
- **WHEN** the portfolio has historical snapshots
- **THEN** the dashboard renders an interactive SVG chart comparing Portfolio Equity Growth % against SPY Benchmark Growth % over time, with hover tooltips displaying date, portfolio value, and relative alpha.

#### Scenario: Inspect Active Holdings and Trigger Manual Liquidation
- **WHEN** a user views the Active Holdings table on `/portfolio`
- **THEN** the table displays each open position with Ticker, Archetype badge, Entry Date, Entry Price, Current Price, Unrealized PnL ($ and %), Holding Days, and a "Close Position" button.
- **WHEN** the user clicks "Close Position" and confirms
- **THEN** the frontend sends a close request to `/api/portfolio/positions/{id}/close` and updates the active positions and trade journal upon completion.

#### Scenario: Inspect Trade Journal
- **WHEN** a user views the Trade Journal table on `/portfolio`
- **THEN** the table displays historical closed trades with Ticker, Archetype, Entry Date, Exit Date, Holding Days, Exit Reason (`STOP_LOSS`, `TAKE_PROFIT`, `TIME_EXIT`, `MANUAL`), Realized PnL, Return %, and SPY Alpha %.

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
