## MODIFIED Requirements

### Requirement: Shared Navigation Header
The frontend dashboard and all sub-routes SHALL feature a persistent, styled navigation header bar to switch between the main Dashboard (Retail Momentum), Smart Money & Gov, Cross-Engine Synthesis Matrix, Historical Reports, and Ticker Analytics.

#### Scenario: Navigate Pages
- **WHEN** a user clicks on "Retail Momentum", "Smart Money & Gov", "Synthesis Matrix", "Historical Reports", or "Ticker Analytics" links in the header
- **THEN** the router navigates the user to the corresponding page.

## ADDED Requirements

### Requirement: Display Smart Money & Political Scout View
The frontend dashboard SHALL provide a dedicated Smart Money view (`/smart-money`) displaying Engine 2 picks and individual catalyst reports (`/smart-money/[ticker]`).

#### Scenario: View Smart Money Feed
- **WHEN** the user navigates to `/smart-money`
- **THEN** they see ranked cards displaying high-conviction insider cluster buys, Congressional trades, committee relevance tags, dollar volumes, and catalyst time horizons.

#### Scenario: View Smart Money Individual Report
- **WHEN** the user opens `/smart-money/[ticker]`
- **THEN** they see an Inflow Ledger detailing executive and political transactions, legislative catalyst research, and a medium-term swing thesis.

### Requirement: Display Cross-Engine Synthesis Matrix
The frontend dashboard SHALL provide a Synthesis Matrix view (`/synthesis`) displaying market archetype diagnoses and retail awareness measurements.

#### Scenario: View Synthesis Matrix
- **WHEN** the user navigates to `/synthesis`
- **THEN** they see active stocks mapped across the 4 archetypes (The Rocket, The Retail Trap, Silent Accumulation, Market Noise) with retail awareness indicators and actionable divergence callouts.

