import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic_ai import Agent
from app.llm_schemas import CoreIntelSynthesis
from app.market_researcher import (
    fetch_financial_metrics,
    fetch_recent_news,
    fetch_sec_filings,
    fetch_web_search_news,
)
from app.crud import get_latest_core_equity_intel, save_core_equity_intel

logger = logging.getLogger(__name__)

CORE_INTEL_SYSTEM_PROMPT = """
You are a senior fundamental equity research analyst. Your job is to produce an objective, unvarnished Core Equity Intelligence Report on a company.

You are given:
- Real-time financial metrics and valuation ratios
- Recent SEC EDGAR filings (10-K, 10-Q, 8-K)
- Curated corporate and industry news headlines
- Targeted web search queries regarding macro and geopolitical risks

CRITICAL INSTRUCTIONS FOR OUTPUT:
- ground_truth_status: State the company's objective competitive moat, balance sheet health, and market standing based strictly on verifiable data.
- ground_truth_filings_news: Highlight essential operational disclosures, cash flow trends, segment revenue growth, and debt obligations synthesized from SEC filings and news.
- events_happenings: Detail key upcoming catalyst dates, product launches, earnings announcements, supply chain shifts, or geopolitical risks.
- risk_score: Assign 'Low', 'Medium', or 'High' risk based on valuation, balance sheet leverage, and competitive pressures.
- risk_analysis: Provide a concise 2-3 sentence justification explaining the chosen risk score.
- actionable_insight: Give a concrete, trackable financial metric, catalyst horizon, or regulatory milestone for investors to monitor.

Do not invent financial data or hallucinate numbers. If data is missing or ambiguous, state that clearly and reflect the uncertainty in the risk score.
"""

if not os.getenv("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = "mock_key"

core_intel_agent = Agent(
    'google:gemini-4-argon',
    output_type=CoreIntelSynthesis,
    system_prompt=CORE_INTEL_SYSTEM_PROMPT
)


async def research_core_equity_intel(
    ticker: str,
    db: Optional[AsyncSession] = None,
    force_refresh: bool = False
) -> dict:
    """
    Gathers fundamental metrics, SEC filings, and news, synthesizing a standardized
    CoreEquityIntel record. If already generated in the database within 6 hours, reuses the cached record.
    """
    ticker_clean = ticker.upper()
    logger.info(f"Conducting Core Equity Intel research for ${ticker_clean}...")

    # Step 1: Check existing record if db session is provided (deduplication)
    if db and not force_refresh:
        existing = await get_latest_core_equity_intel(db, ticker_clean)
        if existing and existing.date:
            now_utc = datetime.now(timezone.utc)
            # Make sure timezone aware
            rec_date = existing.date if existing.date.tzinfo else existing.date.replace(tzinfo=timezone.utc)
            if now_utc - rec_date < timedelta(hours=6):
                logger.info(f"Reusing cached Core Equity Intel for ${ticker_clean} (id={existing.id})")
                return {
                    "id": existing.id,
                    "ticker": existing.ticker,
                    "date": existing.date.isoformat(),
                    "company_name": existing.company_name,
                    "sector": existing.sector,
                    "industry": existing.industry,
                    "current_price": existing.current_price,
                    "target_price": existing.target_price,
                    "ground_truth_status": existing.ground_truth_status,
                    "ground_truth_filings_news": existing.ground_truth_filings_news,
                    "events_happenings": existing.events_happenings,
                    "risk_score": existing.risk_score,
                    "risk_analysis": existing.risk_analysis,
                    "actionable_insight": existing.actionable_insight,
                    "raw_metrics": existing.raw_metrics or {},
                    "raw_news": existing.raw_news or [],
                    "raw_filings": existing.raw_filings or [],
                }

    # Step 2: Fetch raw market and regulatory intelligence
    metrics = fetch_financial_metrics(ticker_clean)
    news = fetch_recent_news(ticker_clean)
    filings = fetch_sec_filings(ticker_clean)
    web_news = fetch_web_search_news(ticker_clean)

    # Format prompt text
    sec_filings_text = "No SEC filings retrieved."
    if filings:
        sec_filings_text = "\n".join([
            f"- {f.get('date', 'N/A')} ({f.get('type', 'Filing')}): {f.get('title', '')} (EDGAR: {f.get('edgarUrl', '')})"
            for f in filings
        ])

    metrics_text = f"""
Current Price: {metrics.get('current_price')}
Target Mean Price: {metrics.get('target_price')}
Market Cap: {metrics.get('market_cap')}
Trailing P/E: {metrics.get('pe_ratio')}
Forward P/E: {metrics.get('forward_pe')}
52-Week Range: {metrics.get('fifty_two_week_low')} - {metrics.get('fifty_two_week_high')}
Industry: {metrics.get('industry')}
Sector: {metrics.get('sector')}
"""

    news_text = "\n".join([f"- {item.get('title', '')} ({item.get('link', '')})" for item in news]) if news else "No recent standard news found."
    web_news_text = "\n".join([f"- {item.get('title', '')}: {item.get('body', '')}" for item in web_news]) if web_news else "No web search news found."

    prompt = f"""
Conduct Core Fundamental Equity Intelligence Research on stock ticker: {ticker_clean}

=== [FINANCIAL & VALUATION RATIOS] ===
{metrics_text}

=== [SEC EDGAR FILINGS (10-K, 10-Q, 8-K)] ===
{sec_filings_text}

=== [STANDARD FINANCIAL NEWS HEADLINES] ===
{news_text}

=== [WEB SEARCH MACRO & CATALYST CONTEXT] ===
{web_news_text}
"""

    try:
        response = await core_intel_agent.run(prompt)
        synthesis = response.output
    except Exception as e:
        logger.warning(f"Gemini Core Intel synthesis fallback for ${ticker_clean}: {e}")
        synthesis = CoreIntelSynthesis(
            ground_truth_status=f"Objective industry positioning for {ticker_clean} in {metrics.get('sector', 'General')}.",
            ground_truth_filings_news=sec_filings_text[:400] if filings else "Standard corporate filings.",
            events_happenings="Routine business operations and macroeconomic monitoring.",
            risk_score="Medium",
            risk_analysis="Standard market volatility with baseline corporate risk.",
            actionable_insight="Monitor upcoming quarterly earnings release."
        )

    intel_payload = {
        "ticker": ticker_clean,
        "company_name": metrics.get("short_name") or metrics.get("long_name") or ticker_clean,
        "sector": metrics.get("sector") or "General",
        "industry": metrics.get("industry") or "General",
        "current_price": metrics.get("current_price"),
        "target_price": metrics.get("target_price"),
        "ground_truth_status": synthesis.ground_truth_status,
        "ground_truth_filings_news": synthesis.ground_truth_filings_news,
        "events_happenings": synthesis.events_happenings,
        "risk_score": synthesis.risk_score,
        "risk_analysis": synthesis.risk_analysis,
        "actionable_insight": synthesis.actionable_insight,
        "raw_metrics": metrics,
        "raw_news": news,
        "raw_filings": filings,
    }

    # Persist if db is provided
    if db:
        saved_record = await save_core_equity_intel(db, intel_payload)
        intel_payload["id"] = saved_record.id
        intel_payload["date"] = saved_record.date.isoformat() if saved_record.date else datetime.now(timezone.utc).isoformat()

    return intel_payload

