## 1. Environment & Configuration

- [x] 1.1 Ensure configuration handles `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, and configurable `REDDIT_SUBREDDITS` (defaulting to `wallstreetbets,stocks,ValueInvesting`).

## 2. Reddit OAuth Client & Scraper Implementation

- [x] 2.1 Implement `RedditOAuthClient` in `backend/app/reddit_scraper.py` with Application-Only Client Credentials token generation and fail-fast exception handling on missing/invalid credentials.
- [x] 2.2 Implement multi-subreddit listing fetcher querying `/r/{sub}/top?t=day` and `/r/{sub}/hot` via `https://oauth.reddit.com`.
- [x] 2.3 Implement comments fetcher querying `/comments/{id}` via `https://oauth.reddit.com` preserving real `score` and author/body metadata.
- [x] 2.4 Assemble `scrape_reddit_data()` async function to iterate across subreddits, collect posts and comments, and return normalized payload with authentic upvote scores.

## 3. Pipeline Integration & Verification

- [x] 3.1 Update `backend/app/pipeline.py` to seamlessly integrate multi-subreddit scraping and verify downstream ticker ranking with authentic scores.
- [x] 3.2 Update or add automated tests in `backend/tests/test_reddit_scraper.py` testing auth validation, mock API responses, and fail-fast behavior.
- [x] 3.3 Execute live verification test fetching posts from `r/wallstreetbets`, `r/stocks`, and `r/ValueInvesting`.

## 4. Documentation & OpenSpec Validation

- [x] 4.1 Update `backend/README.md` and root `README.md` to document the OAuth multi-subreddit scraper architecture.
- [x] 4.2 Run `openspec validate multi-subreddit-oauth-scraper --strict` to verify all spec artifacts.
