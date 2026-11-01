## MODIFIED Requirements

### Requirement: Scrape Bounded Target Subreddit
The system SHALL fetch the daily top posts and top comments across configured target subreddits (`r/wallstreetbets`, `r/stocks`, `r/ValueInvesting`) using Reddit's Application-Only OAuth API (`https://oauth.reddit.com`).

#### Scenario: Scheduled Execution
- **WHEN** the daily scheduled time is reached
- **THEN** the scraper requests an OAuth access token using `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET`, queries each configured target subreddit for top/hot posts over the last 24 hours, and fetches top comments for each thread.

#### Scenario: Missing or Invalid Credentials
- **WHEN** `REDDIT_CLIENT_ID` or `REDDIT_CLIENT_SECRET` is missing, invalid, or rejected during OAuth token generation
- **THEN** the system SHALL immediately raise an authentication error and halt the pipeline, without attempting unauthenticated or RSS fallback.

### Requirement: Respect Reddit Rate Limits
The system SHALL respect Reddit OAuth API rate limits (100 requests per minute) by tracking rate limit headers (`x-ratelimit-remaining` and `x-ratelimit-reset`).

#### Scenario: Quota Exhausted
- **WHEN** a response indicates `x-ratelimit-remaining` is below 1
- **THEN** the scraper pauses execution for `x-ratelimit-reset + 1` seconds before issuing subsequent requests.

#### Scenario: Rate Limited
- **WHEN** an OAuth API request receives an HTTP 429 response
- **THEN** the scraper waits for the duration specified by `x-ratelimit-reset` and retries up to 3 times before failing the request.

### Requirement: Extract and Rank Stock Tickers
The system SHALL parse the text across all scraped subreddits to identify stock tickers and rank them using authentic engagement weighting based on post upvotes, comment upvotes, and mention frequency.

#### Scenario: Top Tickers Selection
- **WHEN** extraction is complete across all scraped subreddits
- **THEN** the system calculates each candidate ticker's engagement score as $(\text{Mentions in Post} \times \text{Post Score}) + (\text{Mentions in Comment} \times \text{Comment Score})$ using real Reddit upvote data and isolates the top-scoring tickers for downstream analysis.

#### Scenario: Scores Unavailable
- **WHEN** posts and comments are sourced from Reddit's OAuth API
- **THEN** genuine upvote scores are present on all returned posts and comments, and scores are never artificially hardcoded to 1.
