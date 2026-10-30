# ticker-analytics Specification

## Purpose
Provides comprehensive time-series analytics, trajectory visualizations, and historical intelligence tracking across pipeline runs for individual stock tickers, including on-demand AI meta-analysis.

## Requirements

### Requirement: Historical Ticker Catalog API
The backend API SHALL provide an endpoint listing all unique stock tickers that have at least one persisted report in the database.

#### Scenario: Fetch Tracked Tickers
- **WHEN** a client sends a GET request to `/api/analytics/tickers`
- **THEN** the API returns a JSON array of all unique ticker symbols stored in the database sorted alphabetically.

### Requirement: Ticker Historical Analytics Time-Series API
The backend API SHALL provide an endpoint returning chronological historical metrics and reports for a specified ticker.

#### Scenario: Fetch Ticker History
- **WHEN** a client sends a GET request to `/api/analytics/ticker/{ticker}`
- **THEN** the API returns a JSON list of historical data points sorted by date ascending, each containing:
  - `date`: Timestamp of the report
  - `current_price`: Market price recorded at report generation
  - `target_price`: Analyst mean target price
  - `recommendation`: The AI signal (`BUY`, `HOLD`, `SELL`)
  - `community_sentiment`: Sentiment percentage/descriptor
  - `reconciliation_risk_score`: Assessed risk score (`Low`, `Medium`, `High`)
  - `reconciliation_actionable_insight`: Trackable metric or event
  - `raw_metrics`: Financial ratios snapshot (P/E ratio, 52-week range, market cap)

#### Scenario: Ticker Not Found
- **WHEN** a client requests analytics for a ticker with no historical data
- **THEN** the API returns a 404 HTTP status code with an appropriate error message.

### Requirement: On-Demand Cached AI Trajectory Meta-Analysis
The system SHALL provide an on-demand AI meta-analysis that synthesizes multi-run historical data for a ticker to evaluate thesis progression, sentiment divergence, and catalyst follow-through, caching results in the database.

#### Scenario: Return Cached Meta-Analysis
- **WHEN** a client requests the meta-analysis for a ticker and a valid cached analysis exists corresponding to the latest report
- **THEN** the backend immediately returns the cached meta-analysis without invoking the LLM.

#### Scenario: Generate New Meta-Analysis
- **WHEN** a client requests meta-analysis for a ticker with $\ge 2$ historical reports and no up-to-date cache exists (or `force_refresh=true` is requested)
- **THEN** the backend invokes Gemini to generate a structured `TrajectoryAnalysis` (synthesizing sentiment-vs-price divergence, thesis progression, and follow-through), saves it to the database, and returns it.

#### Scenario: Insufficient Historical Data
- **WHEN** a client requests meta-analysis for a ticker with fewer than 2 historical reports
- **THEN** the API returns an informative message indicating that at least 2 historical pipeline runs are required for trajectory meta-analysis.

### Requirement: Interactive Ticker Analytical Dashboard
The frontend SHALL provide a dedicated Ticker Analytics page (`/analytics`) allowing users to select a ticker and inspect its multi-run analytics and AI meta-analysis.

#### Scenario: Select Ticker
- **WHEN** a user navigates to `/analytics` and chooses a ticker symbol from a selector or list
- **THEN** the view loads and renders the ticker's historical analytical report.

#### Scenario: View Price vs Target Price Chart
- **WHEN** the ticker historical analytics view is rendered
- **THEN** an interactive time-series chart plots historical Current Price and Target Price over time across all recorded runs.

#### Scenario: View Recommendation and Sentiment Timeline
- **WHEN** viewing the ticker analytics page
- **THEN** a chronological timeline displays how AI recommendations and community sentiment evolved across report dates.

#### Scenario: View Actionable Insights Log
- **WHEN** viewing the ticker analytics page
- **THEN** a chronological log of previous actionable insights and catalysts is presented.

#### Scenario: View AI Trajectory Meta-Analysis
- **WHEN** viewing a ticker with $\ge 2$ historical reports
- **THEN** an AI Trajectory Meta-Analysis card displays divergence detection, catalyst follow-through, and a button to generate/refresh analysis.
