# reddit-scraper Specification

## Purpose
TBD - created by archiving change subreddit-stock-analyzer. Update Purpose after archive.
## Requirements
### Requirement: Scrape Bounded Target Subreddit
The system SHALL fetch strictly the top 20 posts and the top 50 comments per post from a specified subreddit over the last 24 hours.

#### Scenario: Scheduled Execution
- **WHEN** the daily scheduled time is reached
- **THEN** the scraper hits the `.json` endpoint using an HTTP client (`httpx` or `requests`) with a custom User-Agent, pulling the bounded dataset (max 20 posts, 1000 comments) and implementing strict `asyncio.sleep` delays between comment requests to avoid rate limits.

### Requirement: Scraping Fallback Mechanism
The system SHALL automatically fall back to an HTML scraper parsing listings and comments from `old.reddit.com` if the `.json` requests get blocked with a 403 Forbidden or 429 Too Many Requests response.

#### Scenario: Fallback Scraping
- **WHEN** a `.json` request receives a client error (e.g. 403 Blocked)
- **THEN** the system logs a warning and issues an HTTP GET to `https://old.reddit.com/r/{subreddit}/` with custom user-agent, parsing listings and thread comments using regular expressions or an HTML parser, maintaining the 1.5s sleep interval.

### Requirement: Extract and Rank Stock Tickers
The system SHALL parse the text to identify stock tickers and rank them using a weighted engagement heuristic (e.g., Mentions * Upvotes).

#### Scenario: Top Tickers Selection
- **WHEN** extraction is complete
- **THEN** the system isolates the top scoring tickers for the day.

### Requirement: Bundle Ticker Context
The system SHALL aggregate the specific posts and comments that mentioned each of the top tickers to provide exact context to the LLM.

#### Scenario: Context Bundling
- **WHEN** the top tickers are identified
- **THEN** the system creates a textual payload for each ticker containing only the Reddit text relevant to that ticker.

