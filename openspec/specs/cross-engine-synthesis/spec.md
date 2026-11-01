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

