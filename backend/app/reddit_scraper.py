import os
import time
import asyncio
import logging
from typing import List, Dict, Any, Optional
import httpx
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Default subreddits to scrape
DEFAULT_SUBREDDITS = ["wallstreetbets", "stocks", "ValueInvesting"]
DEFAULT_USER_AGENT = "python:stock-picker:v1.0.0 (by /u/stock-picker-bot)"

OAUTH_TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
OAUTH_BASE_URL = "https://oauth.reddit.com"


class RedditAuthError(RuntimeError):
    """Raised when Reddit API credentials are missing, invalid, or rejected."""
    pass


class RedditAPIError(RuntimeError):
    """Raised when Reddit OAuth API calls fail repeatedly or encounter unrecoverable errors."""
    pass


def get_target_subreddits() -> List[str]:
    """
    Returns the list of target subreddits from REDDIT_SUBREDDITS env var
    or defaults to ['wallstreetbets', 'stocks', 'ValueInvesting'].
    """
    raw = os.getenv("REDDIT_SUBREDDITS", "")
    if raw.strip():
        return [s.strip().removeprefix("r/").removeprefix("/") for s in raw.split(",") if s.strip()]
    return list(DEFAULT_SUBREDDITS)


class RedditOAuthClient:
    """
    Client for interacting with the official Reddit API using
    Application-Only OAuth (Client Credentials Grant).
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        self.client_id = client_id or os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("REDDIT_CLIENT_SECRET")
        self.user_agent = user_agent or os.getenv("REDDIT_USER_AGENT", DEFAULT_USER_AGENT)
        
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0

        # Strict validation: Fail fast if credentials are not configured
        if not self.client_id or not self.client_secret:
            raise RedditAuthError(
                "Reddit OAuth credentials missing: REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET "
                "must be configured in the environment / .env file."
            )

    async def get_access_token(self, client: httpx.AsyncClient) -> str:
        """
        Retrieves a valid OAuth access token, requesting a new one if expired.
        Fails fast if credentials are rejected.
        """
        now = time.time()
        # Reuse cached token if it has more than 60 seconds of validity left
        if self._access_token and (self._token_expires_at - now) > 60:
            return self._access_token

        auth = httpx.BasicAuth(self.client_id, self.client_secret)
        headers = {"User-Agent": self.user_agent}
        data = {"grant_type": "client_credentials"}

        try:
            logger.info("Requesting Reddit OAuth access token (client credentials grant)...")
            res = await client.post(OAUTH_TOKEN_URL, auth=auth, data=data, headers=headers)
        except Exception as e:
            raise RedditAuthError(f"Network error connecting to Reddit OAuth token service: {e}") from e

        if res.status_code in (401, 403):
            raise RedditAuthError(
                f"Reddit OAuth authentication rejected (HTTP {res.status_code}): "
                "Invalid REDDIT_CLIENT_ID or REDDIT_CLIENT_SECRET."
            )
        
        if res.status_code != 200:
            raise RedditAuthError(
                f"Reddit OAuth token request failed (HTTP {res.status_code}): {res.text}"
            )

        token_data = res.json()
        if "access_token" not in token_data:
            raise RedditAuthError(f"Unexpected token response from Reddit: {token_data}")

        self._access_token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 3600)
        self._token_expires_at = now + expires_in
        logger.info(f"Reddit OAuth token obtained successfully (expires in {expires_in}s).")
        return self._access_token

    async def _request(
        self,
        endpoint: str,
        client: httpx.AsyncClient,
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
    ) -> Any:
        """
        Issues an authenticated GET request to Reddit's OAuth API with rate-limit handling.
        """
        url = f"{OAUTH_BASE_URL}/{endpoint.lstrip('/')}"
        
        for attempt in range(1, max_retries + 1):
            token = await self.get_access_token(client)
            headers = {
                "Authorization": f"Bearer {token}",
                "User-Agent": self.user_agent,
            }

            res = await client.get(url, headers=headers, params=params)

            # Check rate limit headers
            remaining = res.headers.get("x-ratelimit-remaining")
            reset = float(res.headers.get("x-ratelimit-reset", 1))

            if res.status_code == 429:
                logger.warning(f"Reddit OAuth rate limit reached (429). Sleeping {reset + 0.5:.1f}s (attempt {attempt})")
                await asyncio.sleep(reset + 0.5)
                continue

            if res.status_code == 401:
                logger.warning("Reddit OAuth token expired or invalidated. Invalidating cache and retrying...")
                self._access_token = None
                continue

            if res.status_code != 200:
                raise RedditAPIError(f"Reddit API request failed [{res.status_code}] for {url}: {res.text}")

            if remaining is not None and float(remaining) < 1:
                logger.debug(f"Reddit rate-limit quota low ({remaining} left), waiting {reset:.1f}s")
                await asyncio.sleep(reset)

            return res.json()

        raise RedditAPIError(f"Exceeded {max_retries} attempts requesting {url}")

    async def fetch_subreddit_posts(
        self,
        subreddit: str,
        client: httpx.AsyncClient,
        limit: int = 15,
        sort: str = "hot",
    ) -> List[Dict[str, Any]]:
        """
        Fetches top or hot posts for a specific subreddit.
        """
        endpoint = f"/r/{subreddit}/{sort}"
        params = {"limit": limit, "t": "day"}
        data = await self._request(endpoint, client, params=params)

        posts = []
        children = data.get("data", {}).get("children", [])
        for child in children:
            p = child.get("data", {})
            # Ignore stickied moderator / rules posts
            if p.get("stickied", False):
                continue
            posts.append({
                "id": p.get("id"),
                "title": p.get("title", ""),
                "selftext": p.get("selftext", ""),
                "score": p.get("score", 1),
                "num_comments": p.get("num_comments", 0),
                "upvote_ratio": p.get("upvote_ratio", 1.0),
                "subreddit": p.get("subreddit", subreddit),
                "permalink": p.get("permalink", ""),
                "url": p.get("url", ""),
                "created_utc": p.get("created_utc"),
                "comments": [],
            })

        logger.info(f"Fetched {len(posts)} non-stickied posts from r/{subreddit} ({sort})")
        return posts

    async def fetch_post_comments(
        self,
        post_id: str,
        subreddit: str,
        client: httpx.AsyncClient,
        limit: int = 25,
    ) -> List[Dict[str, Any]]:
        """
        Fetches top-level comments for a given post.
        """
        endpoint = f"/r/{subreddit}/comments/{post_id}"
        params = {"limit": limit, "depth": 2, "sort": "top"}
        try:
            data = await self._request(endpoint, client, params=params)
        except Exception as e:
            logger.warning(f"Failed to fetch comments for post {post_id} in r/{subreddit}: {e}")
            return []

        comments = []
        # Reddit returns a list of two listings: [post_listing, comments_listing]
        if isinstance(data, list) and len(data) > 1:
            children = data[1].get("data", {}).get("children", [])
            for child in children:
                if child.get("kind") != "t1":
                    continue
                c = child.get("data", {})
                body = c.get("body", "")
                if body and body != "[deleted]" and body != "[removed]":
                    comments.append({
                        "id": c.get("id"),
                        "body": body,
                        "score": c.get("score", 1),
                        "author": c.get("author", ""),
                    })
        return comments[:limit]


async def fetch_top_posts_and_comments(
    subreddits: Optional[List[str]] = None,
    post_limit: int = 15,
    comment_limit: int = 25,
) -> List[Dict[str, Any]]:
    """
    Main entry point for scraping Reddit discussions across target subreddits using
    official Reddit OAuth.
    
    Strictly fails if credentials are missing or invalid (no RSS fallback).
    """
    target_subs = subreddits or get_target_subreddits()
    oauth_client = RedditOAuthClient()

    all_posts: List[Dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=30.0) as http_client:
        # Pre-verify token to fail fast immediately if credentials are bad
        await oauth_client.get_access_token(http_client)

        for sub in target_subs:
            logger.info(f"Scraping r/{sub} via Reddit OAuth API...")
            try:
                posts = await oauth_client.fetch_subreddit_posts(
                    sub, http_client, limit=post_limit, sort="hot"
                )
                
                # Fetch comments for posts that have comments
                for p in posts:
                    if p.get("num_comments", 0) > 0:
                        p["comments"] = await oauth_client.fetch_post_comments(
                            p["id"], sub, http_client, limit=comment_limit
                        )
                all_posts.extend(posts)
            except Exception as e:
                logger.error(f"Error scraping r/{sub}: {e}")
                # If error was an auth error, re-raise to fail fast
                if isinstance(e, RedditAuthError):
                    raise

    logger.info(
        f"Completed multi-subreddit scraping: Total {len(all_posts)} posts collected from {target_subs}."
    )
    return all_posts


# Alias for spec naming consistency
scrape_reddit_data = fetch_top_posts_and_comments
