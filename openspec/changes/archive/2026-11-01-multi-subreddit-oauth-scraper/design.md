## Context

See `proposal.md` for motivation. The codebase currently uses `backend/app/reddit_scraper.py` which scrapes Atom/RSS feeds using `httpx`. The user has registered an official Reddit script application and added `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` to `backend/.env`.

## Goals / Non-Goals

**Goals:**
- Implement an authenticated Reddit OAuth client using standard `httpx.AsyncClient` using the Application-Only Client Credentials flow.
- Scrape daily top/hot posts and top comments across `r/wallstreetbets`, `r/stocks`, and `r/ValueInvesting`.
- Populate real `score` (net upvotes) and `num_comments` on posts and comments, directly restoring weighted scoring in `ticker_extractor.py`.
- Fail immediately if credentials are missing or authentication fails (no RSS fallback).
- Keep scraping execution under 15 seconds.

**Non-Goals:**
- Adding `praw` as an external dependency (async `httpx` already in use and lighter).
- User actions (upvoting, commenting, user OAuth login) - read-only public data extraction only.
- Indefinite comment recursion - fetch top-level comments up to limit (e.g., top 15-25 comments per high-engagement post) to remain fast and bounded.

## Decisions

### Decision 1: Lightweight `httpx` Client Credentials flow over `praw`
- **Choice**: Direct async HTTP calls to `https://www.reddit.com/api/v1/access_token` with Basic Auth, caching the bearer token in memory with expiry buffer.
- **Rationale**: Keeps dependencies simple and native to `uv` / `asyncio`. PRAW is synchronous and heavy.
- **Alternative considered**: PRAW / AsyncPRAW. Rejected due to extraneous dependencies and configuration complexity.

### Decision 2: Configurable Multi-Subreddit Target List
- **Choice**: Scrape a defined set of subreddits: `["wallstreetbets", "stocks", "ValueInvesting"]` (configurable via `REDDIT_SUBREDDITS` env var, defaulting to all three).
- **Rationale**: WSB captures retail sentiment and high-beta momentum, `r/stocks` captures broader market news and earnings plays, and `r/ValueInvesting` captures fundamental quality businesses. Combining them broadens discovery while avoiding noise.

### Decision 3: Fail-Fast Authentication Guard
- **Choice**: On initialization, if `REDDIT_CLIENT_ID` or `REDDIT_CLIENT_SECRET` is unset, or if token retrieval returns 401/403, raise `RedditAuthError` immediately and halt the pipeline.
- **Rationale**: User explicitly requested strict failure without falling back to RSS, ensuring configuration problems are visible immediately.

### Decision 4: Preserving Downstream Contract with `ticker_extractor.py`
- **Choice**: Format extracted posts as:
  ```python
  {
      "id": post["id"],
      "title": post["title"],
      "selftext": post["selftext"],
      "score": post["score"],
      "subreddit": post["subreddit"],
      "comments": [
          {"id": c["id"], "body": c["body"], "score": c["score"]}
      ]
  }
  ```
- **Rationale**: `ticker_extractor.py` already consumes this exact dictionary shape and natively computes `(Mentions * Post Score) + (Mentions * Comment Score)`. No refactoring of extraction logic is needed.

## Risks / Trade-offs

- [Risk] Reddit token expires mid-run → [Mitigation] Bearer tokens last 86,400s (24h). The client checks token validity before requests and refreshes if expiring within 5 minutes.
- [Risk] One subreddit has network or permission glitch → [Mitigation] Log error for the affected subreddit and proceed with the remaining subreddits unless all fail.
- [Risk] Rate limit 429 response → [Mitigation] Read `x-ratelimit-reset` header and retry up to 3 times, although 100 req/min is well beyond our bounded pipeline requirement (~30-50 requests total).

