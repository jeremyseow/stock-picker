import asyncio
import logging
import os
from dotenv import load_dotenv

from app.database import init_db, AsyncSessionLocal
from app.reddit_scraper import fetch_top_posts_and_comments
from app.ticker_extractor import get_ranked_tickers_with_context
from app.market_researcher import fetch_financial_metrics, fetch_recent_news, fetch_sec_filings, fetch_web_search_news, is_valid_ticker
from app.agent import generate_stock_report
from app.crud import save_daily_tickers, save_ticker_report

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_pipeline():
    load_dotenv()
    
    logger.info("Initializing database...")
    await init_db()
    
    logger.info("Step 1: Scraping Reddit...")
    posts = await fetch_top_posts_and_comments(post_limit=20, comment_limit=50)
    
    if not posts:
        logger.error("No posts found or API error. Exiting.")
        return
        
    logger.info("Step 2: Extracting Tickers...")
    candidate_tickers = get_ranked_tickers_with_context(posts)
    logger.info(f"Found {len(candidate_tickers)} raw candidate tickers from Reddit.")
    
    top_tickers = []
    for item in candidate_tickers:
        ticker = item["ticker"]
        if is_valid_ticker(ticker):
            top_tickers.append(item)
            if len(top_tickers) == 5:
                break
                
    logger.info(f"Selected {len(top_tickers)} valid tickers for analysis: {[t['ticker'] for t in top_tickers]}")
    
    async with AsyncSessionLocal() as db:
        await save_daily_tickers(db, top_tickers)
        
        for item in top_tickers:
            ticker = item["ticker"]
            logger.info(f"Step 3: Researching {ticker}...")
            
            metrics = fetch_financial_metrics(ticker)
            news = fetch_recent_news(ticker)
            
            # Fetch SEC filings
            filings = fetch_sec_filings(ticker)
            if filings:
                sec_filings_text = "\n".join([
                    f"- {f['date']} ({f['type']}): {f['title']} (URL: {f['edgarUrl']})"
                    for f in filings
                ])
            else:
                sec_filings_text = "No recent SEC filings found."
                
            # Fetch Web Search news
            search_hits = fetch_web_search_news(ticker)
            if search_hits:
                web_search_text = "\n".join([
                    f"- {s['title']} (Link: {s['link']})\n  Snippet: {s['snippet']}"
                    for s in search_hits
                ])
            else:
                web_search_text = "No recent web search news found."
            
            logger.info(f"Step 4: Generating Report for {ticker}...")
            report = await generate_stock_report(ticker, metrics, news, item["context_text"], sec_filings_text, web_search_text)
            
            logger.info(f"Step 5: Saving {ticker} report ({report.recommendation})...")
            await save_ticker_report(db, ticker, report, metrics, news)

    logger.info("Pipeline completed successfully!")

if __name__ == "__main__":
    asyncio.run(run_pipeline())
