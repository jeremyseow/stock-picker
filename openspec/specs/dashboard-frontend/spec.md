# dashboard-frontend Specification

## Purpose
TBD - created by archiving change subreddit-stock-analyzer. Update Purpose after archive.

## Requirements

### Requirement: Shared Navigation Header
The frontend dashboard and all sub-routes SHALL feature a persistent, styled navigation header bar to switch between the main Dashboard, Historical Reports, and Ticker Analytics.

#### Scenario: Navigate Pages
- **WHEN** a user clicks on "Historical Reports", "Ticker Analytics", or "Dashboard" link in the header
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
The frontend dashboard SHALL allow the user to click on a stock ticker to view its detailed generated research report.

#### Scenario: View Report Details
- **WHEN** a user clicks on a specific stock from the daily list
- **THEN** a detailed view opens, displaying:
  - **Hero Header**: Ticker symbol, Sector/Industry, current price vs target price, and calculated potential upside percentage (`+XX.X%`).
  - **Analyst Callout**: Rationale and immediate actionable insight highlighted prominently.
  - **Four Pillar Analysis Grid**:
    1. **Community Sentiment**: Sentiment score + detailed hype discussion.
    2. **Ground Truth**: Clean paragraphs for Corporate Position and Filings/News Analysis.
    3. **Events & Happenings**: Key corporate/industry events, launches, or macro happenings (wars, conflicts).
    4. **AI Reconciliation**: Risk level badge + reconciliation analysis.
  - **Financial Ratios Grid**: Trailing P/E, forward P/E, 52-week high/low.
  - **Corporate News headlines list**: Render raw news articles as clickable external links (if links exist).

### Requirement: Display Date-Selected Historical Reports
The frontend dashboard SHALL provide a Historical Reports view that enables users to view all available pipeline run dates and display the intelligence reports generated on a selected date.

#### Scenario: View Available Dates
- **WHEN** the user navigates to the Historical Reports view
- **THEN** the interface fetches and presents a list or picker of all historical run dates.

#### Scenario: Select Date and View Reports
- **WHEN** the user selects a specific date
- **THEN** the dashboard fetches and renders report preview cards for each ticker analyzed on that date, showing ticker symbol, recommendation badge, price, target price, and industry.

#### Scenario: No Reports for Date
- **WHEN** the user selects a date that has no recorded reports
- **THEN** a clear informative message is displayed stating no reports are available for that date.
