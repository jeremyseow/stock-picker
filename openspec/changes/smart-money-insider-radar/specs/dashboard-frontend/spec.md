## MODIFIED Requirements

### Requirement: Display Individual Stock Report
The frontend dashboard SHALL allow the user to click on a stock ticker to view its detailed generated research report, including the Smart Money & Insider Trading Radar.

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
  - **Smart Money & Insider Trading Radar**:
    - 6-Month Net Insider Flow gauge (Net Buying vs. Net Selling indicator with dollar volumes).
    - Recent Form 4 transactions table displaying transaction dates, executive names, executive positions, share count, dollar value, and transaction badge (Buy/Sell).
    - Congressional and Senate trade disclosure summary.
    - AI Smart Money Divergence verdict callout.
  - **Financial Ratios Grid**: Trailing P/E, forward P/E, 52-week high/low.
  - **Corporate News headlines list**: Render raw news articles as clickable external links (if links exist).

