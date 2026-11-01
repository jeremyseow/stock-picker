## MODIFIED Requirements

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

## ADDED Requirements

### Requirement: Standardized API Namespacing and Unified Link Terminology
The application SHALL provide consistently namespaced endpoints and unified link labels across all user interfaces.

#### Scenario: Query Namespaced Endpoints
- **WHEN** a client requests data for Retail Momentum, Smart Money Scout, Cross-Engine Synthesis, or Master Reports
- **THEN** the backend serves consistently namespaced paths:
  - `/api/retail/reports` and `/api/retail/report/{ticker}` (Engine 1)
  - `/api/smart-money/reports` and `/api/smart-money/report/{ticker}` (Engine 2)
  - `/api/synthesis/reports` and `/api/synthesis/latest` (Cross-Engine)
  - `/api/master/report/{ticker}` and `/api/reports/{ticker}` (Unified Master Report)

