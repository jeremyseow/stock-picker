import logging
import asyncio
from dotenv import load_dotenv

from app.database import init_db, AsyncSessionLocal
from app.reddit_scraper import fetch_top_posts_and_comments
from app.ticker_extractor import get_ranked_tickers_with_context
from app.market_researcher import (
    fetch_financial_metrics,
    fetch_recent_news,
    fetch_sec_filings,
    fetch_web_search_news,
    is_valid_ticker,
)
from app.agent import generate_stock_report
from app.core_intel_engine import research_core_equity_intel
from app.crud import (
    save_daily_tickers,
    save_retail_social_raw,
    save_retail_sentiment_report,
    get_smart_money_verdict_for_ticker,
)
from app.telegram_notifier import send_daily_digest

logger = logging.getLogger(__name__)
_retail_pipeline_lock = asyncio.Lock()


async def run_retail_pipeline():
    """
    Executes Engine 1 (Retail Momentum Scout):
    1. Scrapes Reddit discussion posts & comments.
    2. Extracts and scores trending tickers.
    3. Persists raw social signals to retail_social_raw and daily_tickers.
    4. Attaches Core Equity Intel and generates Retail Sentiment Reports.
    5. Dispatches Telegram daily digest.
    """
    if _retail_pipeline_lock.locked():
        logger.warning("Engine 1 (Retail Momentum) is already running. Skipping concurrent run.")
        return

    async with _retail_pipeline_lock:
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
        
        processed_summaries = []

        async with AsyncSessionLocal() as db:
            await save_retail_social_raw(db, top_tickers)
            saved_daily_tickers = await save_daily_tickers(db, top_tickers)

            for idx, item in enumerate(top_tickers):
                ticker = item["ticker"]
                logger.info(f"Step 3: Conducting Core Intel research for {ticker}...")
                core_intel = await research_core_equity_intel(ticker, db=db)

                metrics = core_intel.get("raw_metrics") or fetch_financial_metrics(ticker)
                news = core_intel.get("raw_news") or fetch_recent_news(ticker)
                filings = core_intel.get("raw_filings") or fetch_sec_filings(ticker)

                if filings:
                    sec_filings_text = "\n".join([
                        f"- {f['date']} ({f['type']}): {f['title']} (URL: {f['edgarUrl']})"
                        for f in filings
                    ])
                else:
                    sec_filings_text = "No recent SEC filings found."

                search_hits = fetch_web_search_news(ticker)
                if search_hits:
                    web_search_text = "\n".join([
                        f"- {s['title']} (Link: {s['link']})\n  Snippet: {s['snippet']}"
                        for s in search_hits
                    ])
                else:
                    web_search_text = "No recent web search news found."

                core_summary = (
                    f"Ground Truth: {core_intel.get('ground_truth_status', '')}\n"
                    f"Risk Score: {core_intel.get('risk_score', 'Medium')} - {core_intel.get('risk_analysis', '')}\n"
                    f"Key Events: {core_intel.get('events_happenings', '')}"
                )

                logger.info(f"Step 4: Generating Retail Overlay for {ticker}...")
                report = await generate_stock_report(
                    ticker,
                    metrics,
                    news,
                    item["context_text"],
                    sec_filings_text,
                    web_search_text,
                    core_intel_summary=core_summary,
                )

                logger.info(f"Step 5: Saving {ticker} retail report ({report.recommendation})...")
                daily_ticker_id = saved_daily_tickers[idx].id if idx < len(saved_daily_tickers) else None
                await save_retail_sentiment_report(
                    db,
                    ticker,
                    report,
                    core_intel_id=core_intel.get("id"),
                    daily_ticker_id=daily_ticker_id,
                )

                e2_verdict = await get_smart_money_verdict_for_ticker(db, ticker)
                processed_summaries.append({
                    "rank": idx + 1,
                    "ticker": ticker,
                    "recommendation": report.recommendation,
                    "current_price": metrics.get("current_price"),
                    "target_price": metrics.get("target_price"),
                    "smart_money_verdict": e2_verdict,
                    "actionable_insight": report.reconciliation_actionable_insight,
                })
                
        logger.info("Step 6: Sending Telegram daily digest...")
        await send_daily_digest(processed_summaries)

        logger.info("Retail pipeline completed successfully!")
