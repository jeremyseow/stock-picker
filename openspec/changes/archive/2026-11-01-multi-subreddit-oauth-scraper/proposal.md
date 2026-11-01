## Why

The current scraper relies on unauthenticated Reddit RSS/Atom feeds which strip out upvote scores and comment counts (forcing all scores to 1), restrict discovery to a single subreddit, and enforce severe rate limits (1 req/min, stretching runs to ~20 minutes). With developer API credentials registered, migrating to official Reddit OAuth restores authentic engagement scores, multi-subreddit sentiment discovery across `r/wallstreetbets`, `r/stocks`, and `r/ValueInvesting`, and sub-minute execution speeds.

## What Changes

- **Official Reddit OAuth Integration**: Authenticate via Reddit's Application-Only OAuth (Client Credentials Grant) using `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET`.
- **Multi-Subreddit Scraping**: Expand scraping coverage to extract daily top/hot posts and top discussions across `r/wallstreetbets`, `r/stocks`, and `r/ValueInvesting`.
- **Restoration of Weighted Scoring**: Re-enable true engagement scoring ($Mentions \times Score$) using authentic upvote scores on posts and comments, along with upvote ratios.
- **Fail-Fast Error Handling**: Strict requirement that if Reddit API credentials are missing, expired, or invalid, the scraper fails immediately with an explicit error (no silent fallback to RSS).
- **Execution Speed**: Drastically reduce scraping run time from ~20 minutes to under 15 seconds leveraging Reddit's 100 req/min API allowance.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `reddit-scraper`: Upgrade from single-subreddit RSS scraping with hardcoded scores to multi-subreddit OAuth scraping with authentic upvote scores, comment trees, and strict failure on invalid credentials.

## Impact

- **Backend**:
  - `backend/app/reddit_scraper.py`: Replace RSS Atom parsing with authenticated Reddit OAuth API requests (`https://oauth.reddit.com`).
  - `backend/app/config.py` / `pipeline.py`: Enforce presence of `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET`.
  - `backend/app/ticker_extractor.py`: Leverages restored `score` values directly in existing engagement formulas.
- **Dependencies**: No external PRAW bloat required; standard `httpx` or `requests` using client credentials grant.
- **Environment**: Requires `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` in `backend/.env`.
- **Specs & Tests**: Update `reddit-scraper` spec and test suites.

