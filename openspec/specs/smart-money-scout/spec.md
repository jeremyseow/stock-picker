# smart-money-scout Specification

## Purpose
Ingests, filters, and ranks market-wide corporate insider purchases and Congressional STOCK Act trading disclosures, identifying high-conviction medium-term swing catalysts through macroeconomic and political research.

## Requirements

### Requirement: Ingest Market-Wide Form 4 and Congressional Filings
The system SHALL ingest public daily SEC Form 4 insider filings and Congressional STOCK Act Periodic Transaction Reports (House and Senate PTRs).

#### Scenario: Ingestion Execution
- **WHEN** the daily Smart Money ingestion job runs
- **THEN** the system fetches recent Form 4 filings and Congressional disclosures, parsing transaction types, insider roles, transaction values, and filing dates.

### Requirement: Filter and Score Smart Money Conviction
The system SHALL filter out non-cash transactions and calculate a multi-factor conviction score for each ticker based on role seniority, cluster buying intensity, and Congressional committee jurisdiction overlap.

#### Scenario: Transaction Code Filtering
- **WHEN** parsing Form 4 transactions
- **THEN** the system accepts only open-market cash purchases (Code P) and excludes option exercises, grants, gifts, and pre-scheduled 10b5-1 selling plans.

#### Scenario: Multi-Factor Scoring
- **WHEN** scoring candidate tickers
- **THEN** the system applies a 3.0x multiplier for C-suite buyers, up to a 2.5x multiplier for cluster buying (≥3 insiders within 7 days), and a 3.0x multiplier when a politician's committee jurisdiction directly matches the ticker's sector, ranking the top 5 highest-conviction tickers.

### Requirement: Conduct Macro and Political Research
The system SHALL dispatch a research agent to investigate legislative catalysts, government contracts, and regulatory milestones for top-ranked smart money candidates, attaching a Smart Money Overlay to the shared Core Equity Intel report and serving the complete fundamental ground truth alongside the catalyst analysis.

#### Scenario: Research Synthesis
- **WHEN** top smart money candidate tickers are selected and fundamental core intel is assembled
- **THEN** the system queries recent bills, committee calendars, contract awards, and disclosure filings to produce a specialized Smart Money Overlay with projected catalyst horizons and an actionable swing thesis.

#### Scenario: Self-Contained Catalyst Intelligence Delivery
- **WHEN** a client queries an individual smart money report via `/api/smart-money/report/{ticker}`
- **THEN** the response includes both the Smart Money Overlay (inflow ledger, committee overlap, catalyst horizon, swing thesis) and the complete Core Equity Intelligence payload (valuation multiples, SEC 10-Q/8-K ground truth, corporate positioning, and risk scores).
