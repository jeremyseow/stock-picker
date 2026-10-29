import httpx
import os
import re
import html
import asyncio
import logging
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Custom User-Agent (configurable via .env)
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) HermesAgent/1.1 (Autonomous Research Project)"
USER_AGENT = os.getenv("REDDIT_USER_AGENT", DEFAULT_USER_AGENT)
HEADERS = {"User-Agent": USER_AGENT}

BASE_URL = "https://www.reddit.com"
ATOM_NS = {"a": "http://www.w3.org/2005/Atom"}
MAX_ATTEMPTS = 4

# NOTE (2026-10): Reddit now blocks unauthenticated JSON endpoints (403 "Blocked") and
# redirects old.reddit.com to a login page (302 reason=lor2). The public Atom/RSS feeds
# still work but are heavily rate limited (~1 request per 60s for logged-out clients),
# and they do not expose upvote scores or comment counts.


async def fetch_rss(url: str, client: httpx.AsyncClient) -> list:
    """
    Fetches a Reddit Atom feed and returns its <entry> elements.
    Honours Reddit's x-ratelimit-* headers: on 429 it waits and retries, and when the
    remaining quota hits 0 it sleeps until the window resets so the next call succeeds.
    """
    for attempt in range(1, MAX_ATTEMPTS + 1):
        logger.debug(f"Fetching RSS: {url} (attempt {attempt})")
        response = await client.get(url, headers=HEADERS)
        reset = float(response.headers.get("x-ratelimit-reset", 60))
        remaining = response.headers.get("x-ratelimit-remaining")

        if response.status_code == 429:
            logger.info(f"Rate limited by Reddit, sleeping {reset + 1:.0f}s before retry")
            await asyncio.sleep(reset + 1)
            continue

        response.raise_for_status()
        entries = ET.fromstring(response.text).findall("a:entry", ATOM_NS)

        if remaining is not None and float(remaining) < 1:
            logger.info(f"Rate-limit quota exhausted, sleeping {reset + 1:.0f}s")
            await asyncio.sleep(reset + 1)
        return entries

    raise RuntimeError(f"Exceeded {MAX_ATTEMPTS} attempts fetching {url} (rate limited)")


def html_to_text(raw: str) -> str:
    """Strips HTML tags/entities from feed content."""
    if not raw:
        return ""
    # Prefer the markdown body if present (drops "submitted by /u/x [link] [comments]" boilerplate)
    md_match = re.search(r'<div class="md">(.*?)</div>', raw, re.DOTALL)
    if md_match:
        raw = md_match.group(1)
    elif "submitted by" in raw:
        return ""
    text = re.sub(r"<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def _entry_text(entry: ET.Element, tag: str) -> str:
    el = entry.find(f"a:{tag}", ATOM_NS)
    return (el.text or "") if el is not None else ""


def parse_post_entry(entry: ET.Element) -> dict:
    link_el = entry.find("a:link", ATOM_NS)
    link = link_el.attrib.get("href", "") if link_el is not None else ""
    return {
        "id": _entry_text(entry, "id").removeprefix("t3_"),
        "title": html.unescape(_entry_text(entry, "title")).strip(),
        "selftext": html_to_text(_entry_text(entry, "content")),
        "score": 1,  # Not available via RSS; extractor falls back to mention counting
        "num_comments": None,  # Not available via RSS
        "permalink": link.removeprefix(BASE_URL),
        "comments": [],
    }


def parse_comment_entries(entries: list) -> list:
    comments = []
    for entry in entries:
        entry_id = _entry_text(entry, "id")
        if not entry_id.startswith("t1_"):
            continue  # First entry is the post itself
        body = html_to_text(_entry_text(entry, "content"))
        if body:
            comments.append({"id": entry_id.removeprefix("t1_"), "body": body, "score": 1})
    return comments


async def fetch_top_posts_and_comments(subreddit_name="wallstreetbets", post_limit=20, comment_limit=50):
    """
    Fetches the top `post_limit` posts from the last 24 hours plus their top comments
    via Reddit's public RSS feeds. Expect roughly 1 minute per request due to rate limits.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        top_url = f"{BASE_URL}/r/{subreddit_name}/top/.rss?t=day&limit={post_limit}"
        try:
            logger.info(f"Fetching top posts via RSS: {top_url}")
            posts_data = [parse_post_entry(e) for e in await fetch_rss(top_url, client)][:post_limit]
        except Exception as e:
            logger.error(f"Failed to fetch posts via RSS: {e}")
            return []

        logger.info(f"Fetched {len(posts_data)} posts; fetching comments (rate limited, ~1 min/post)")
        for i, post in enumerate(posts_data, 1):
            permalink = post["permalink"] or f"/r/{subreddit_name}/comments/{post['id']}/"
            comments_url = f"{BASE_URL}{permalink.rstrip('/')}/.rss?sort=top&limit={comment_limit}"
            try:
                entries = await fetch_rss(comments_url, client)
                post["comments"] = parse_comment_entries(entries)[:comment_limit]
                logger.info(f"[{i}/{len(posts_data)}] {len(post['comments'])} comments for post {post['id']}")
            except Exception as e:
                logger.error(f"Failed to fetch comments for post {post['id']}: {e}")

    return posts_data
