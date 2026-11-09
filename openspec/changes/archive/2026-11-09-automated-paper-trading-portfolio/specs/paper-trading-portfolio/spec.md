## Purpose

Automates trade execution and risk management for high-conviction synthesis signals with a simulated $100,000 capital ledger, automated market-open entries, stop-loss and take-profit exits, time-decay holding limits, and S&P 500 alpha benchmarking.

## ADDED Requirements

### Requirement: Portfolio Account and Capital Allocation
The system SHALL maintain a paper trading portfolio account initialized with \$100,000 virtual cash. The system SHALL allocate a fixed \$10,000 (10% of initial capital) per new trade position. The system SHALL enforce a strict maximum concurrency cap of 10 active positions at any time.

#### Scenario: Default Account Initialization
- **WHEN** the portfolio service starts and no account exists
- **THEN** the system SHALL initialize a default account with \$100,000.00 cash balance, \$0 invested capital, and \$100,000.00 total equity.

#### Scenario: Position Allocation Sizing
- **WHEN** an eligible synthesis signal is selected for entry and cash balance is at least \$10,000
- **THEN** the system SHALL calculate the share quantity as `floor(10000 / entry_price)` and deduct the allocated cost from available cash.

#### Scenario: Maximum Concurrent Position Queue Discipline
- **WHEN** 10 positions are currently open and new eligible synthesis signals are generated
- **THEN** the system SHALL skip execution for new candidate signals until existing positions are closed and free up capacity.

### Requirement: Automated US Market Open Order Execution
The system SHALL execute pending high-conviction synthesis orders automatically at US Market Open (09:30 ET / 22:30 SGT) on trading days, fetching opening prices from real market data.

#### Scenario: High Conviction Order Qualification
- **WHEN** a synthesis report records an archetype of `The Rocket` or `Silent Accumulation` with an Overall Score of 75.0 or higher from the latest pipeline run
- **THEN** the system SHALL qualify the ticker as a pending order candidate for the next market open.

#### Scenario: Market Open Execution Fill
- **WHEN** the market open execution job runs at 09:30 ET on a market trading day
- **THEN** the system SHALL fetch the current market opening price for qualified tickers via `yfinance`, fill the order, record the entry date and price, and transition the position to `OPEN`.

#### Scenario: Insufficient Cash for Order
- **WHEN** an eligible ticker is queued but available cash is less than \$10,000
- **THEN** the system SHALL log an insufficient funds event and skip execution without partial allocation.

### Requirement: Automated US Market Close Exit Rules
The system SHALL evaluate all open positions daily at US Market Close (16:00 ET / 05:00 SGT) against strict stop-loss, take-profit, and holding-horizon criteria, closing violating positions at the closing price.

#### Scenario: Hard Stop-Loss Triggered
- **WHEN** the closing price of an open position represents a loss of 7.0% or greater relative to the entry price (`(close - entry) / entry <= -0.07`)
- **THEN** the system SHALL close the position with exit reason `STOP_LOSS`, return the recovered proceeds to portfolio cash, and log the realized loss.

#### Scenario: Take-Profit Target Triggered
- **WHEN** the closing price of an open position represents a gain of 15.0% or greater relative to the entry price (`(close - entry) / entry >= 0.15`), or reaches the research target price
- **THEN** the system SHALL close the position with exit reason `TAKE_PROFIT`, return proceeds to portfolio cash, and log the realized gain.

#### Scenario: Maturation Horizon Time Exit
- **WHEN** an open position reaches its maximum archetype holding horizon (8 trading days for `The Rocket`, 22 trading days for `Silent Accumulation`) without hitting stop or take-profit targets
- **THEN** the system SHALL close the position with exit reason `TIME_EXIT` at the closing price and credit the proceeds to portfolio cash.

#### Scenario: Position Stays Open
- **WHEN** an open position's return remains between -7.0% and +15.0% and the holding days are below the archetype maximum
- **THEN** the system SHALL keep the position `OPEN` and update its unrealized PnL and current price.

### Requirement: Manual Position Liquidation
The system SHALL provide an administrative endpoint allowing the user to immediately liquidate any open position at the latest market price.

#### Scenario: User Manually Closes Position
- **WHEN** a user submits a manual close request for an active position ID
- **THEN** the system SHALL fetch the latest available market price, close the position with exit reason `MANUAL`, update realized PnL and return percentage, credit the portfolio cash, and return the updated position record.

#### Scenario: Manual Close on Closed Position
- **WHEN** a user submits a manual close request for a position that is already `CLOSED`
- **THEN** the system SHALL return an HTTP 400 Bad Request error indicating the position is not active.

### Requirement: Trade Journal and Performance Alpha Benchmarking
The system SHALL record an immutable journal entry for every closed position, compute excess return over the S&P 500 (SPY) for the identical holding period, and generate daily portfolio equity snapshots.

#### Scenario: Trade Journal Logging with SPY Alpha
- **WHEN** a position is closed (via stop-loss, take-profit, time exit, or manual liquidation)
- **THEN** the system SHALL record entry date, exit date, entry price, exit price, realized dollar PnL, return percentage, SPY benchmark return over the exact holding window, and excess alpha percentage (`position_return - spy_return`).

#### Scenario: Daily Portfolio Snapshot Capture
- **WHEN** the daily market close position evaluation finishes
- **THEN** the system SHALL calculate total portfolio value (`cash + sum(open_positions_market_value)`), fetch SPY closing price, and insert a new record into `portfolio_snapshots`.

### Requirement: Historical Trade Bootstrapping
The system SHALL provide a backfill procedure to simulate paper portfolio performance across historical synthesis reports and historical market prices.

#### Scenario: Execute Historical Backfill
- **WHEN** the backfill utility is executed
- **THEN** the system SHALL sequentially replay historical synthesis signals, simulate market-open entries and market-close exits, populate closed trade records, and construct daily historical equity snapshots.

