# reddit-scraper Specification

## Purpose
TBD - created by archiving change subreddit-stock-analyzer. Update Purpose after archive.
## Requirements
### Requirement: Scrape Bounded Target Subreddit
The system SHALL fetch strictly the top 20 posts and the top 50 comments per post from a specified subreddit over the last 24 hours, using Reddit's public Atom/RSS feeds.

> Note (Oct 2026): Reddit returns `403 Blocked` for unauthenticated `.json` endpoints and redirects `old.reddit.com` to a login page (`302 reason=lor2`). The previous JSON-first / `old.reddit.com` HTML fallback approach was removed for this reason.

#### Scenario: Scheduled Execution
- **WHEN** the daily scheduled time is reached (19:00 Asia/Singapore)
- **THEN** the scraper issues an HTTP GET (`httpx`, custom User-Agent) to `https://www.reddit.com/r/{subreddit}/top/.rss?t=day&limit=20`, parses the Atom entries (id, title, body, permalink), and then fetches each post's `{permalink}/.rss?sort=top&limit=50` for comments, skipping the first entry (the post itself).

### Requirement: Respect Reddit Rate Limits
The system SHALL throttle feed requests using Reddit's `x-ratelimit-remaining` and `x-ratelimit-reset` response headers (logged-out quota is roughly 1 request per 60 seconds).

#### Scenario: Quota Exhausted
- **WHEN** a response reports `x-ratelimit-remaining` below 1
- **THEN** the system sleeps for `x-ratelimit-reset + 1` seconds before the next request.

#### Scenario: Rate Limited
- **WHEN** a request returns `429 Too Many Requests`
- **THEN** the system sleeps for `x-ratelimit-reset + 1` seconds and retries, up to 4 attempts, after which it logs an error and skips that feed (a failed top-posts feed aborts the run with no posts).

### Requirement: Extract and Rank Stock Tickers
The system SHALL parse the text to identify stock tickers and rank them using a weighted engagement heuristic (e.g., Mentions * Upvotes).

#### Scenario: Top Tickers Selection
- **WHEN** extraction is complete
- **THEN** the system isolates the top scoring tickers for the day.

#### Scenario: Scores Unavailable
- **WHEN** posts and comments are sourced from RSS feeds (which expose no upvote scores or comment counts)
- **THEN** each post and comment is assigned a score of 1, so ranking is effectively by mention count.

### Requirement: Bundle Ticker Context
The system SHALL aggregate the specific posts and comments that mentioned each of the top tickers to provide exact context to the LLM.

#### Scenario: Context Bundling
- **WHEN** the top tickers are identified
- **THEN** the system creates a textual payload for each ticker containing only the Reddit text relevant to that ticker.

