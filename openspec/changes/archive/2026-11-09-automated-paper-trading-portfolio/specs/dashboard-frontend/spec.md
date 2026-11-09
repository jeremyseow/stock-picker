## MODIFIED Requirements

### Requirement: Shared Navigation Header
The frontend dashboard and all sub-routes SHALL feature a persistent, styled navigation header bar to switch between the main Dashboard (Retail Momentum), Smart Money & Gov, Cross-Engine Synthesis Matrix, Historical Reports, Ticker Analytics, and Paper Trading Portfolio.

#### Scenario: Navigate Pages
- **WHEN** a user clicks on "Retail Momentum", "Smart Money & Gov", "Synthesis Matrix", "Historical Reports", "Ticker Analytics", or "Portfolio" links in the header
- **THEN** the router navigates the user to the corresponding page.

## ADDED Requirements

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

