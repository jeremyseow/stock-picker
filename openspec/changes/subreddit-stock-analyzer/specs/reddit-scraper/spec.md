## ADDED Requirements

### Requirement: Scrape Bounded Target Subreddit
The system SHALL fetch strictly the top 20 posts and the top 50 comments per post from a specified subreddit over the last 24 hours.

#### Scenario: Scheduled Execution
- **WHEN** the daily scheduled time is reached
- **THEN** the scraper hits the `.json` endpoint using an HTTP client (`httpx` or `requests`) with a custom User-Agent, pulling the bounded dataset (max 20 posts, 1000 comments) and implementing strict `asyncio.sleep` delays between comment requests to avoid rate limits.

### Requirement: Extract and Rank Stock Tickers
The system SHALL parse the text to identify stock tickers and rank them using a weighted engagement heuristic (e.g., Mentions * Upvotes).

#### Scenario: Top Tickers Selection
- **WHEN** extraction is complete
- **THEN** the system isolates the top 5 scoring tickers for the day.

### Requirement: Bundle Ticker Context
The system SHALL aggregate the specific posts and comments that mentioned each of the top 5 tickers to provide exact context to the LLM.

#### Scenario: Context Bundling
- **WHEN** the top 5 tickers are identified
- **THEN** the system creates a textual payload for each ticker containing only the Reddit text relevant to that ticker.
