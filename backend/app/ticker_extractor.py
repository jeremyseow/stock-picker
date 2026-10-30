import re
from collections import defaultdict

# Common English words that look like tickers
BLACKLIST = {
    "A", "I", "THE", "ARE", "IT", "TO", "BE", "IN", "ON", "OR", "SO", "AS", "AT", "IF", "WE", 
    "US", "UK", "EU", "UP", "DO", "GO", "NO", "AM", "PM", "CEO", "CFO", "CTO", "YOLO", "FOMO",
    "IMO", "TBH", "DD", "WSB", "ATH", "GDP", "CPI", "FED", "EPS", "PTE", "ROI", "YTD", "Q1", "Q2", "Q3", "Q4",
    "TLDR", "PSA", "RSU", "IPO", "ETF", "USA", "SEC", "IRS", "LLC", "INC", "LTD", "ALL", "FOR", "NOW", "OUT",
    "SEE", "TOO", "WAY", "WHO", "WHY", "YES", "YOU", "NEW", "BUY", "SELL", "CALL", "PUT", "AND", "HAS", "NOT",
    "BUT", "ANY", "CAN", "DID", "GET", "HAD", "HER", "HIM", "HIS", "HOW", "MAN", "MAY", "OUR", "OUT", "SHE",
    "THEY", "WAS", "ONE", "TWO", "SIX", "TEN", "DAY", "RUN", "WOW", "BIG", "BAD", "MAD", "SAD", "GLD", "SLV",
    "AI", "PE"
}

# Ticker aliases mapping secondary share classes or common synonyms to the official primary security
TICKER_ALIASES = {
    "GOOGL": "GOOG",
}

TICKER_REGEX = re.compile(r'\$([A-Z]{1,5})\b|(?<!\$)\b([A-Z]{2,5})\b')

def extract_tickers_from_text(text):
    """
    Extracts potential stock tickers from text based on the specifications.
    Matches $TICKER (1-5 chars) or clean uppercase words (2-5 chars) not preceded by $.
    """
    if not text:
        return []
        
    matches = TICKER_REGEX.findall(text)
    
    tickers = []
    for m in matches:
        # findall returns (dollar_group, clean_group)
        ticker = m[0] or m[1]
        if ticker:
            ticker = TICKER_ALIASES.get(ticker, ticker)
        if ticker and ticker not in BLACKLIST:
            # Filter out single letters unless they are famous (like F, C)
            if len(ticker) == 1 and ticker not in ["F", "C", "V", "O"]:
                continue
            tickers.append(ticker)
            
    return list(set(tickers)) # Unique tickers in this text block

def process_and_rank_tickers(posts_data):
    """
    Takes the fetched Reddit data and scores tickers based on weighted engagement.
    Score = (Mentions in Post) * (Post Score) + (Mentions in Comment) * (Comment Score)
    """
    ticker_scores = defaultdict(float)
    ticker_contexts = defaultdict(list)
    
    for post in posts_data:
        post_score = post.get("score", 1)
        # Extract from title and body
        post_text = f"{post.get('title', '')} {post.get('selftext', '')}"
        post_tickers = extract_tickers_from_text(post_text)
        
        for ticker in post_tickers:
            ticker_scores[ticker] += max(post_score, 1) # Prevent 0 score
            ticker_contexts[ticker].append({
                "type": "post",
                "id": post["id"],
                "text": post_text,
                "score": post_score
            })
            
        for comment in post.get("comments", []):
            comment_score = comment.get("score", 1)
            comment_text = comment.get("body", "")
            comment_tickers = extract_tickers_from_text(comment_text)
            
            for ticker in comment_tickers:
                # Add score weight
                ticker_scores[ticker] += max(comment_score, 1)
                ticker_contexts[ticker].append({
                    "type": "comment",
                    "id": comment["id"],
                    "text": comment_text,
                    "score": comment_score
                })
                
    # Sort tickers by score descending
    ranked_tickers = sorted(ticker_scores.items(), key=lambda x: x[1], reverse=True)
    
    return ranked_tickers, ticker_contexts

def get_ranked_tickers_with_context(posts_data, limit: int = None):
    """
    Returns the ranked tickers and their specific text context bundled.
    If limit is specified, only returns the top `limit` candidates.
    """
    ranked_tickers, ticker_contexts = process_and_rank_tickers(posts_data)
    
    if limit is not None:
        ranked_tickers = ranked_tickers[:limit]
        
    results = []
    
    for ticker, score in ranked_tickers:
        # Bundle context
        context_items = ticker_contexts[ticker]
        # Sort context by score descending so LLM sees most important stuff first
        context_items = sorted(context_items, key=lambda x: x["score"], reverse=True)
        
        # Take top 20 context items max to save token space
        context_items = context_items[:20]
        
        context_text = "\n\n".join([f"[{item['type'].upper()} | Score: {item['score']}]: {item['text']}" for item in context_items])
        
        results.append({
            "ticker": ticker,
            "engagement_score": score,
            "mention_count": len(ticker_contexts[ticker]),
            "context_text": context_text
        })
        
    return results

