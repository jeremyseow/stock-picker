## MODIFIED Requirements

### Requirement: Display Individual Stock Report
The frontend dashboard SHALL allow the user to click on a stock ticker to view its detailed unified master equity research report, dynamically presenting Core Fundamentals, Retail Momentum sentiment, Smart Money inflow catalysts, and Cross-Engine synthesis diagnosis.

#### Scenario: View Report Details
- **WHEN** a user clicks on a stock ticker from any list, feed, or matrix
- **THEN** a detailed unified view opens, displaying:
  - **Master Hero Header**: Ticker symbol, company name, sector/industry, current price vs target price, calculated potential upside percentage, and active signal badges (Retail recommendation and/or Smart Money conviction tier).
  - **Core Fundamentals & Ground Truth Grid**:
    1. **Financial Ratios Grid**: Trailing P/E, forward P/E, 52-week trading range, market cap.
    2. **Ground Truth**: Corporate Position and SEC Filings/News Analysis.
    3. **Events & Happenings**: Key corporate events, product launches, or macro/geopolitical events.
    4. **Risk Assessment**: Risk level badge (Low/Medium/High) and risk factors.
  - **Smart Money & Political Inflow Section**: Inflow ledger table, cluster buying metrics, committee relevance tags, catalyst horizon, and swing thesis (or an informative note if no insider cluster activity exists).
  - **Retail Momentum Section**: Sentiment meter, narrative hype summary, and community expectations (or a stealth notice if retail mentions are near zero).
  - **Synthesis Matrix Diagnosis**: Market archetype badge (The Rocket, Retail Trap, Silent Accumulation, Market Noise) and retail awareness timing edge gauge.

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

## ADDED Requirements

### Requirement: Display Archetype Lifecycle Trajectory in Ticker Analytics
The frontend Ticker Analytics view SHALL display an Archetype Lifecycle Timeline showing how a stock migrated across synthesis archetypes over historical pipeline runs.

#### Scenario: View Archetype Trajectory
- **WHEN** viewing a ticker with historical pipeline reports
- **THEN** an Archetype Progression timeline illustrates the stock's transition between archetypes (e.g. Silent Accumulation to The Rocket to The Retail Trap) with corresponding timing edge scores.
