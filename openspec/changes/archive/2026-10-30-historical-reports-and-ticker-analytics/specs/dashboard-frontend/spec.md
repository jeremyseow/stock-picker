## MODIFIED Requirements

### Requirement: Shared Navigation Header
The frontend dashboard and all sub-routes SHALL feature a persistent, styled navigation header bar to switch between the main Dashboard, Historical Reports, and Ticker Analytics.

#### Scenario: Navigate Pages
- **WHEN** a user clicks on "Historical Reports", "Ticker Analytics", or "Dashboard" link in the header
- **THEN** the router navigates the user to the corresponding page.

## REMOVED Requirements

### Requirement: Display Historical Statistics
**Reason**: Replaced by date-filtered historical intelligence reports view, which is more useful than simple static mention counts.
**Migration**: Use `/stats` (or `/history`) with the date selector to view historical intelligence reports.

## ADDED Requirements

### Requirement: Display Date-Selected Historical Reports
The frontend dashboard SHALL provide a Historical Reports view that enables users to view all available pipeline run dates and display the intelligence reports generated on a selected date.

#### Scenario: View Available Dates
- **WHEN** the user navigates to the Historical Reports view
- **THEN** the interface fetches and presents a list or picker of all historical run dates.

#### Scenario: Select Date and View Reports
- **WHEN** the user selects a specific date
- **THEN** the dashboard fetches and renders report preview cards for each ticker analyzed on that date, showing ticker symbol, recommendation badge, price, target price, and industry.

#### Scenario: No Reports for Date
- **WHEN** the user selects a date that has no recorded reports
- **THEN** a clear informative message is displayed stating no reports are available for that date.

