# cross-engine-synthesis Specification

## Purpose
Synthesizes independent intelligence streams from Retail Momentum (Engine 1) and Smart Money & Political Scout (Engine 2) to diagnose market divergence archetypes, assess retail awareness, and formulate actionable swing theses.

## Requirements

### Requirement: Cross-Engine Ticker Correlation
The system SHALL correlate tickers identified by Retail Momentum with tickers identified by the Smart Money & Political Scout.

#### Scenario: Correlation Execution
- **WHEN** both discovery engines complete daily runs
- **THEN** the system compares retail engagement scores and sentiment against smart money conviction scores and insider flow directions for all active candidates.

### Requirement: Market Archetype Classification
The system SHALL classify correlated stocks into one of four distinct market archetypes: The Rocket (Full Alignment), The Retail Trap (Bearish Divergence), Silent Accumulation (Pre-Catalyst Stealth Entry), or Market Noise.

#### Scenario: Full Alignment Detection
- **WHEN** a stock exhibits high retail engagement alongside heavy insider cluster buying or committee accumulation
- **THEN** the system assigns the archetype "The Rocket" and generates a High-Conviction BUY thesis.

#### Scenario: Retail Trap Detection
- **WHEN** a stock exhibits high retail hype alongside net insider liquidation or politician divestment
- **THEN** the system assigns the archetype "The Retail Trap" and generates an AVOID/SHORT warning.

#### Scenario: Silent Accumulation Detection
- **WHEN** a stock exhibits high smart money conviction while retail mentions on Reddit are near zero
- **THEN** the system assigns the archetype "Silent Accumulation" and generates an early pre-catalyst swing thesis.

### Requirement: Retail Awareness Measurement
The system SHALL quantify a retail awareness metric indicating whether retail traders have detected the smart money catalyst.

#### Scenario: Timing Edge Calculation
- **WHEN** evaluating a smart money candidate
- **THEN** the system outputs a retail awareness indicator showing whether retail mentions are low (high timing edge), rising, or saturated.

### Requirement: Historical Archetype Snapshot Query
The system SHALL provide an API endpoint returning deduplicated synthesis matrix records for a requested historical date.

#### Scenario: Query Archetypes by Historical Date
- **WHEN** a client requests synthesis records for a valid historical date
- **THEN** the system returns all unique tickers classified on that date, sorted by timing edge score descending with archetype labels and divergence diagnoses.

### Requirement: Actionable Contrarian Playbook and Divergence Scorecard
The Cross-Engine Synthesis Master Report SHALL generate and present a Divergence Scorecard comparing Retail Sentiment against Smart Money Conviction alongside an Actionable Contrarian Playbook tailored to the stock's market archetype.

#### Scenario: View Contrarian Playbook
- **WHEN** a synthesis record or master report is viewed for an active stock
- **THEN** the system generates a tailored tactical gameplan containing:
  - **Divergence Heatmap**: Visualizing Retail Sentiment vs. Smart Money Conviction.
  - **Entry Strategy**: Specific accumulation rules (e.g., pre-breakout stealth accumulation vs. riding institutional flow with trailing stops).
  - **Catalyst Horizon**: Target swing duration and key calendar triggers.
  - **Exit Signals**: Concrete liquidation or stop-loss rules (e.g., exit upon retail mention surge or Form 4 disposition filings).
  - **Archetype Lifecycle Vector**: Directional progress indicator through `Silent Accumulation ➔ The Rocket ➔ The Retail Trap ➔ Market Noise`.

### Requirement: Triangulation Matrix Synthesis with Whale Options Flow
The Cross-Engine Synthesis Hub SHALL correlate Engine 1 (Retail Momentum), Engine 2 (Smart Money Scout), and Engine 3 (Whale Options Radar) to diagnose 3-way market positioning and elevate high-conviction stealth trades.

#### Scenario: Correlate Triangulated Flows
- **WHEN** all discovery engines complete daily analysis runs
- **THEN** the system matches retail sentiment, insider cluster buying, and unusual options call sweeps for active candidate tickers.

#### Scenario: Stealth Whales Archetype Elevation
- **WHEN** a stock exhibits high smart money conviction or institutional call sweep volume while retail discussion on Reddit is near zero
- **THEN** the system assigns the archetype "Silent Accumulation (Whale Front-Run)" with a maximum timing edge score (>90.0) and generates an early pre-catalyst tactical swing thesis.
