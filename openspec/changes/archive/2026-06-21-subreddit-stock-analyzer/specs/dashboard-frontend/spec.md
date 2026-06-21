## ADDED Requirements

### Requirement: Shared Navigation Header
The frontend dashboard and all sub-routes SHALL feature a persistent, styled navigation header bar to switch between the main Dashboard and Historical Trends.

#### Scenario: Navigate Pages
- **WHEN** a user clicks on "Historical Trends" or "Dashboard" link in the header
- **THEN** the router navigates the user to the corresponding page.


### Requirement: Display Rich Daily Top Stocks List
The frontend dashboard homepage SHALL display the top highly discussed stocks for the current day as rich preview cards.

#### Scenario: View Daily Stocks
- **WHEN** a user navigates to the dashboard homepage
- **THEN** they see card previews showing:
  - Ticker symbol and rank.
  - An AI recommendation badge (BUY, HOLD, SELL, or NO REPORT) with color indicator.
  - Sector and Industry.
  - Live stock price and target price (if report exists).
  - Reddit mention count and engagement score.

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

### Requirement: Display Historical Statistics
The frontend dashboard SHALL present useful aggregate statistics, such as historically trending tickers.

#### Scenario: View Aggregate Stats
- **WHEN** the user navigates to "Historical Trends"
- **THEN** a table is displayed showing tickers, total mention counts, max engagement scores, and dates scraped.
