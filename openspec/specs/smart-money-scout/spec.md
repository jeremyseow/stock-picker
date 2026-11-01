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
The system SHALL dispatch a research agent to investigate legislative catalysts, government contracts, regulatory milestones, and corporate fundamentals for top-ranked smart money candidates.

#### Scenario: Research Synthesis
- **WHEN** the top 5 smart money tickers are selected
- **THEN** the system queries recent bills, committee calendars, contract awards, and SEC filings to produce a structured Smart Money Intelligence Report with a projected catalyst horizon.

