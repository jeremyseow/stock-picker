## MODIFIED Requirements

### Requirement: Conduct Macro and Political Research
The system SHALL dispatch a research agent to investigate legislative catalysts, government contracts, and regulatory milestones for top-ranked smart money candidates, attaching a Smart Money Overlay to the shared Core Equity Intel report and serving the complete fundamental ground truth alongside the catalyst analysis.

#### Scenario: Research Synthesis
- **WHEN** top smart money candidate tickers are selected and fundamental core intel is assembled
- **THEN** the system queries recent bills, committee calendars, contract awards, and disclosure filings to produce a specialized Smart Money Overlay with projected catalyst horizons and an actionable swing thesis.

#### Scenario: Self-Contained Catalyst Intelligence Delivery
- **WHEN** a client queries an individual smart money report via `/api/smart-money/report/{ticker}`
- **THEN** the response includes both the Smart Money Overlay (inflow ledger, committee overlap, catalyst horizon, swing thesis) and the complete Core Equity Intelligence payload (valuation multiples, SEC 10-Q/8-K ground truth, corporate positioning, and risk scores).

