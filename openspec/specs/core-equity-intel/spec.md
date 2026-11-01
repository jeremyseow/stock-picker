# core-equity-intel Specification

## Purpose
Provides a unified, reusable equity intelligence engine that retrieves valuation metrics, SEC 10-Q/8-K filings, and DuckDuckGo news to synthesize fundamental ground truth sanity checks, events, and risk scores across all candidate tickers from both discovery engines.

## Requirements

### Requirement: Unified Core Equity Intelligence Extraction
The system SHALL execute fundamental market research for every unique candidate stock identified across Engine 1 and Engine 2, extracting valuation ratios, price targets, SEC EDGAR filings, and corporate news.

#### Scenario: Research Candidate Ticker
- **WHEN** a candidate ticker from either discovery engine enters the research pipeline
- **THEN** the system fetches financial metrics, 10-K/10-Q/8-K filings, and recent news articles, synthesizing a fundamental baseline report.

#### Scenario: Cross-Engine Ticker Deduplication
- **WHEN** the same ticker is identified by both Engine 1 and Engine 2 on the same run date
- **THEN** the system executes the Core Equity Intel research exactly once and shares the resulting intel record across both engines.

### Requirement: Ground Truth and Events Synthesis
The system SHALL synthesize qualitative corporate health, balance sheet stability, filings reality checks, and macro/geopolitical events for each candidate ticker using an AI agent.

#### Scenario: Generate Core Intel Synthesis
- **WHEN** market metrics, filings, and news are assembled for a candidate ticker
- **THEN** the AI agent produces Ground Truth status, Filings/News analysis, Key Events & Happenings, and an overall Risk Score (Low, Medium, High).
