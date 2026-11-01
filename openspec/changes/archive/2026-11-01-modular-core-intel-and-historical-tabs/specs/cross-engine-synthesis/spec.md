## ADDED Requirements

### Requirement: Historical Archetype Snapshot Query
The system SHALL provide an API endpoint returning deduplicated synthesis matrix records for a requested historical date.

#### Scenario: Query Archetypes by Historical Date
- **WHEN** a client requests synthesis records for a valid historical date
- **THEN** the system returns all unique tickers classified on that date, sorted by timing edge score descending with archetype labels and divergence diagnoses.

