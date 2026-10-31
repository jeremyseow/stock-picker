import logging
from dotenv import load_dotenv

from app.database import init_db, AsyncSessionLocal
from app.reddit_scraper import fetch_top_posts_and_comments
from app.ticker_extractor import get_ranked_tickers_with_context
from app.market_researcher import (
    fetch_financial_metrics,
    fetch_recent_news,
    fetch_sec_filings,
    fetch_web_search_news,
    fetch_insider_data,
    fetch_congressional_trades,
    is_valid_ticker,
)
from app.agent import generate_stock_report
from app.crud import save_daily_tickers, save_ticker_report
from app.telegram_notifier import send_daily_digest

logger = logging.getLogger(__name__)

async def run_analysis_pipeline():
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
            
            # Fetch Form 4 insider transactions & Congressional disclosures
            insider_data = fetch_insider_data(ticker)
            congressional_trades = fetch_congressional_trades(ticker)

            logger.info(f"Step 4: Generating Report for {ticker}...")
            report = await generate_stock_report(
                ticker,
                metrics,
                news,
                item["context_text"],
                sec_filings_text,
                web_search_text,
                insider_data=insider_data,
                congressional_trades=congressional_trades
            )
            
            logger.info(f"Step 5: Saving {ticker} report ({report.recommendation})...")
            # Enrich insider payload with congressional disclosures and AI synthesis
            enriched_insider_data = dict(insider_data) if insider_data else {"has_data": False}
            enriched_insider_data["congressional_trades"] = congressional_trades or []
            enriched_insider_data["insider_activity_summary"] = report.insider_activity_summary

            await save_ticker_report(db, ticker, report, metrics, news, insider_data=enriched_insider_data)

            processed_summaries.append({
                "rank": item.get("rank", len(processed_summaries) + 1),
                "ticker": ticker,
                "recommendation": report.recommendation,
                "current_price": metrics.get("current_price"),
                "target_price": metrics.get("target_price"),
                "smart_money_verdict": report.smart_money_verdict,
                "actionable_insight": report.reconciliation_actionable_insight
            })
            
    logger.info("Step 6: Sending Telegram daily digest...")
    await send_daily_digest(processed_summaries)

    logger.info("Pipeline completed successfully!")
