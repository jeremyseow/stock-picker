## ADDED Requirements

### Requirement: Display Daily Top Stocks List
The frontend dashboard SHALL display a list or grid of the top highly discussed stocks for the current day.

#### Scenario: View Daily Stocks
- **WHEN** a user navigates to the dashboard homepage
- **THEN** they see the list of top tickers along with their rank and basic metrics (e.g., mention count, current price).

### Requirement: Display Individual Stock Report
The frontend dashboard SHALL allow the user to click on a stock ticker to view its detailed generated research report.

#### Scenario: View Report Details
- **WHEN** a user clicks on a specific stock from the daily list
- **THEN** a detailed view opens, displaying the synthesized industry overview, news, sentiment, potential, and the Buy/Sell recommendation.

### Requirement: Display Historical Statistics
The frontend dashboard SHALL present useful aggregate statistics, such as historically trending tickers over the week or month.

#### Scenario: View Aggregate Stats
- **WHEN** the user navigates to a "Statistics" or "Trends" section
- **THEN** charts or tables are displayed showing ticker mention trends over a 7-day or 30-day period.
