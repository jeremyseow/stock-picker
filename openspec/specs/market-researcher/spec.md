# market-researcher Specification

## Purpose
TBD - created by archiving change subreddit-stock-analyzer. Update Purpose after archive.
## Requirements
### Requirement: Ticker Validation Filter
The system SHALL validate raw ticker symbols before generating reports. A ticker is only considered valid if a query to `yfinance` returns a valid market price (`currentPrice` or `regularMarketPrice`) and a non-empty market capitalization (`marketCap`).

#### Scenario: Ticker Filtering
- **WHEN** a list of candidate symbols is extracted
- **THEN** the system checks each against `yfinance`, discarding non-stock noise (e.g. `OP`, `CNBC`, `CALLS`, `JUST`) and index ETFs (e.g. `SPY`, `QQQ`), keeping only the top 5 valid stock securities.

### Requirement: Fetch Financial Data, SEC Filings, and Web Search
For each of the selected tickers, the system SHALL query `yfinance` for key financial ratios (P/E ratio, forward P/E, 52-week range), the last 5 SEC filings (10-K, 10-Q, 8-K), SEC Form 4 insider transaction statistics (net purchases/sales over last 6 months and recent detailed transactions), and execute a DuckDuckGo web search to gather latest industry news, product launches, and Congressional/Senate STOCK Act disclosure reports.

#### Scenario: Multi-source Research
- **WHEN** provided with a valid ticker
- **THEN** the system successfully gathers financial metrics, SEC filings dates/titles/URLs, SEC Form 4 insider transactions, standard news, and DuckDuckGo text snippets (including corporate events and politician trade reports).

### Requirement: Synthesize Events & Happenings and Reconciliation Report
The system SHALL utilize Pydantic AI to synthesize all information into a structured report mapping to the following distinct pillars:
- **Community Sentiment**: Reddit sentiment score and hype discussion.
- **Ground Truth**: Industry standing and SEC filings/news analysis.
- **Smart Money & Insider Flow**: Summary of recent Form 4 insider buying/selling, net dollar volume, executive positions, and Congressional trade disclosures.
- **Events & Happenings**: Key corporate/industry events, product launches, tech advancements, or macro happenings (wars, conflicts).
- **AI Reconciliation**: Risk score, reconciliation analysis comparing retail hype with fundamental corporate reality, and Smart Money Divergence analysis (identifying whether retail is buying into C-suite distribution).

#### Scenario: Report Synthesis
- **WHEN** all data is collected
- **THEN** the system generates a structured JSON report matching the `StockReport` schema, containing Smart Money insights and divergence analysis.

### Requirement: Strict 'Default to HOLD' Signal
The generated research report SHALL include a BUY, SELL, or HOLD recommendation. The prompt MUST instruct the LLM to default to "HOLD" unless overwhelming, corroborating positive or negative signals exist across all data sources. If corporate insiders (CEOs, CFOs, Directors) are engaged in heavy net selling into a retail rally, the model MUST NOT output a "BUY" recommendation.

#### Scenario: Conservative Signal Generation
- **WHEN** the report is generated with mixed or mild signals
- **THEN** the model outputs a "HOLD" recommendation.

#### Scenario: Heavy Insider Selling Blocks BUY
- **WHEN** retail social sentiment is overwhelmingly bullish but Form 4 disclosures show heavy net insider selling
- **THEN** the model flags the divergence and restricts the recommendation to "HOLD" or "SELL".

### Requirement: LLM Evaluations
The system SHALL include an evaluation suite using unit tests (pytest) to programmatically test the accuracy, consistency, and adherence to the "Default to HOLD" rule of the LLM prompts.

#### Scenario: Running Regressions
- **WHEN** the test command `pytest` is executed
- **THEN** it runs predefined test cases to verify the LLM's adherence to the default-to-hold policy.

