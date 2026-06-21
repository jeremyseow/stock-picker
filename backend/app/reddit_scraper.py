import httpx
import os
import re
from dotenv import load_dotenv
import logging
import asyncio
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

load_dotenv()
logger = logging.getLogger(__name__)

# Mandatory custom User-Agent from spec
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) HermesAgent/1.1 (Autonomous Research Project)"
USER_AGENT = os.getenv("REDDIT_USER_AGENT", DEFAULT_USER_AGENT)
HEADERS = {"User-Agent": USER_AGENT}

# Retry logic: retry on HTTP status errors (like 429) up to 3 times, with exponential backoff
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(httpx.HTTPStatusError),
    reraise=True
)
async def fetch_json(url: str, client: httpx.AsyncClient) -> dict:
    logger.debug(f"Fetching JSON: {url}")
    response = await client.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(httpx.HTTPStatusError),
    reraise=True
)
async def fetch_html(url: str, client: httpx.AsyncClient) -> str:
    logger.debug(f"Fetching HTML: {url}")
    response = await client.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.text

def parse_posts(html: str) -> list:
    """
    Parses listing pages of old.reddit.com to extract post details.
    """
    blocks = html.split('<div class=" thing id-t3_')
    posts = []
    
    for block in blocks[1:]:
        fullname_match = re.search(r'^([a-zA-Z0-9]+)', block)
        post_id = fullname_match.group(1) if fullname_match else None
        
        permalink_match = re.search(r'data-permalink="([^"]+)"', block)
        permalink = permalink_match.group(1) if permalink_match else ""
        
        score_match = re.search(r'data-score="(\d+)"', block)
        score = int(score_match.group(1)) if score_match else 1
        
        comments_match = re.search(r'data-comments-count="(\d+)"', block)
        num_comments = int(comments_match.group(1)) if comments_match else 0
        
        title_match = re.search(r'<a[^>]*class="[^"]*title[^"]*"[^>]*>(.*?)</a>', block)
        title = ""
        if title_match:
            title = re.sub(r'<[^>]*>', '', title_match.group(1))
            title = title.replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
            title = title.strip()
            
        if post_id and permalink:
            posts.append({
                "id": post_id,
                "title": title,
                "permalink": permalink,
                "score": score,
                "num_comments": num_comments,
                "selftext": "",
                "comments": []
            })
            
    return posts

def parse_post_page(html: str) -> tuple:
    """
    Parses comment pages of old.reddit.com to extract selftext and comments.
    """
    post_blocks = html.split('<div class=" thing id-t3_')
    selftext = ""
    if len(post_blocks) > 1:
        post_block = post_blocks[1]
        if "usertext-body" in post_block:
            md_match = re.search(r'<div class="md">(.*?)</div>\s*</form>', post_block, re.DOTALL)
            if not md_match:
                md_match = re.search(r'<div class="md">(.*?)</div>', post_block, re.DOTALL)
            if md_match:
                selftext = re.sub(r'<[^>]*>', '', md_match.group(1))
                selftext = selftext.replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
                selftext = selftext.strip()
                
    comment_blocks = html.split('<div class=" thing id-t1_')
    comments = []
    
    for block in comment_blocks[1:]:
        fullname_match = re.search(r'^([a-zA-Z0-9]+)', block)
        c_id = fullname_match.group(1) if fullname_match else None
        
        score_match = re.search(r'<span[^>]*class="[^"]*score\s+unvoted"[^>]*title="(-?\d+)"', block)
        score = int(score_match.group(1)) if score_match else 1
        
        body_match = re.search(r'<div class="md">(.*?)</div>\s*</form>', block, re.DOTALL)
        if not body_match:
            body_match = re.search(r'<div class="md">(.*?)</div>', block, re.DOTALL)
            
        body = ""
        if body_match:
            raw_body = body_match.group(1)
            body = re.sub(r'<[^>]*>', '', raw_body)
            body = body.replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
            body = body.strip()
            
        if c_id and body:
            comments.append({
                "id": c_id,
                "body": body,
                "score": score
            })
            
    return selftext, comments

async def fetch_top_posts_and_comments(subreddit_name="wallstreetbets", post_limit=20, comment_limit=50):
    """
    Fetches the top `post_limit` posts from the last 24 hours.
    Prioritizes JSON endpoints, and falls back to old.reddit.com scraping if 403 or 429 are returned.
    """
    posts_data = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Fetch Top Posts
        top_json_url = f"https://www.reddit.com/r/{subreddit_name}/top.json?t=day&limit={post_limit}"
        using_json = True
        
        try:
            logger.info(f"Attempting to fetch top posts via JSON: {top_json_url}")
            top_res = await fetch_json(top_json_url, client)
            children = top_res.get("data", {}).get("children", [])
            for item in children:
                post_raw = item.get("data", {})
                posts_data.append({
                    "id": post_raw.get("id"),
                    "title": post_raw.get("title", ""),
                    "selftext": post_raw.get("selftext", ""),
                    "score": post_raw.get("score", 1),
                    "upvote_ratio": post_raw.get("upvote_ratio", 1.0),
                    "num_comments": post_raw.get("num_comments", 0),
                    "permalink": post_raw.get("permalink", ""),
                    "comments": []
                })
        except Exception as e:
            logger.warning(f"Failed to fetch posts via JSON ({e}). Falling back to old.reddit.com scraper.")
            using_json = False
            top_html_url = f"https://old.reddit.com/r/{subreddit_name}/"
            try:
                html_text = await fetch_html(top_html_url, client)
                posts_data = parse_posts(html_text)[:post_limit]
            except Exception as html_err:
                logger.error(f"Failed to fetch posts via old.reddit.com: {html_err}")
                return []
                
        # Step 2: Fetch Comments for each post
        for post in posts_data:
            post_id = post["id"]
            if post.get("num_comments", 0) <= 0:
                continue
                
            # Politely sleep for 1.5s to avoid rate limiting
            logger.info(f"Sleeping 1.5s before fetching comments for post {post_id}")
            await asyncio.sleep(1.5)
            
            # Formulate permalink
            permalink = post.get("permalink", "")
            if not permalink:
                permalink = f"/r/{subreddit_name}/comments/{post_id}/"
                
            if using_json:
                comments_json_url = f"https://www.reddit.com/r/{subreddit_name}/comments/{post_id}.json?sort=top&limit={comment_limit}"
                try:
                    comments_res = await fetch_json(comments_json_url, client)
                    if len(comments_res) > 1:
                        comment_children = comments_res[1].get("data", {}).get("children", [])
                        for c_item in comment_children:
                            if c_item.get("kind") != "t1":
                                continue
                            c_raw = c_item.get("data", {})
                            post["comments"].append({
                                "id": c_raw.get("id"),
                                "body": c_raw.get("body", ""),
                                "score": c_raw.get("score", 1)
                            })
                except Exception as e:
                    logger.warning(f"Failed to fetch comments via JSON for {post_id} ({e}). Falling back to old.reddit.com comments scraper.")
                    # Fallback to HTML comments scraping
                    comments_html_url = f"https://old.reddit.com{permalink}"
                    try:
                        comments_html = await fetch_html(comments_html_url, client)
                        selftext, parsed_comments = parse_post_page(comments_html)
                        post["selftext"] = selftext
                        post["comments"] = parsed_comments[:comment_limit]
                    except Exception as html_err:
                        logger.error(f"HTML fallback failed for comments on post {post_id}: {html_err}")
            else:
                # Direct HTML scraping
                comments_html_url = f"https://old.reddit.com{permalink}"
                try:
                    comments_html = await fetch_html(comments_html_url, client)
                    selftext, parsed_comments = parse_post_page(comments_html)
                    post["selftext"] = selftext
                    post["comments"] = parsed_comments[:comment_limit]
                except Exception as html_err:
                    logger.error(f"HTML scraping failed for comments on post {post_id}: {html_err}")
                    
    return posts_data
