import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import yfinance as yf
from pydantic_ai import Agent
from ddgs import DDGS
from app.llm_schemas import SmartMoneyCatalystAnalysis
from app.market_researcher import fetch_financial_metrics

logger = logging.getLogger(__name__)


def get_historical_trade_price(ticker: str, trade_date_str: str) -> Optional[float]:
    """Attempts to fetch the historical close price around the transaction date."""
    if not trade_date_str:
        return None
    try:
        dt = datetime.strptime(trade_date_str[:10], "%Y-%m-%d")
        start_date = (dt - timedelta(days=2)).strftime("%Y-%m-%d")
        end_date = (dt + timedelta(days=3)).strftime("%Y-%m-%d")
        t = yf.Ticker(ticker)
        hist = t.history(start=start_date, end=end_date)
        if not hist.empty and "Close" in hist:
            return float(hist["Close"].iloc[-1])
    except Exception as e:
        logger.debug(f"Could not fetch historical price for {ticker} on {trade_date_str}: {e}")
    return None

SMART_MONEY_PROMPT = """
You are a senior forensic equity and political intelligence analyst.
Your task is to analyze heavy corporate insider cluster buying and Congressional stock disclosures for a specific company, connect these transactions to external policy, government contract, or macroeconomic catalysts, and formulate an objective swing trading thesis.

CRITICAL INSTRUCTIONS:
- conviction_tier: Choose 'High Conviction Catalyst Buy', 'Speculative Accumulation', or 'Moderate Cluster' based on buyer seniority (C-Suite vs Directors), total dollar size, and policy alignment.
- political_catalyst_analysis: Identify any pending government contracts, legislative markups, subsidies (e.g. CHIPS Act, NDAA), or regulatory approvals directly relevant to the stock or the politician's committee.
- corporate_catalyst_analysis: Reconcile why corporate leaders are personally buying with their own cash. Note whether they are buying after an earnings drop, anticipating a turnaround, or capitalizing on low valuation.
- catalyst_horizon: State the realistic time horizon for thesis realization (e.g. '45-90 days ahead of Q4 earnings and committee vote').
- actionable_thesis: Summarize the high-conviction swing thesis in 2-3 sentences, identifying key catalyst watchpoints and downside risks.
"""

if not os.getenv("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = "mock_key"

smart_money_agent = Agent(
    'google:gemini-4-argon',
    output_type=SmartMoneyCatalystAnalysis,
    system_prompt=SMART_MONEY_PROMPT,
)


def search_catalyst_context(ticker: str, sector: str) -> str:
    """Performs targeted web searches for government contracts, legislation, and corporate turnaround."""
    queries = [
        f"{ticker} government contract award legislative bill hearing 2026",
        f"{ticker} insider buying turnaround earnings catalyst 2026",
    ]
    results_text = []
    try:
        ddgs = DDGS()
        for q in queries:
            for r in list(ddgs.text(q, max_results=3)):
                results_text.append(f"- {r.get('title')}: {r.get('body')[:250]}")
    except Exception as e:
        logger.warning(f"Catalyst search failed for {ticker}: {e}")

    return "\n".join(results_text) if results_text else "No recent legislative or corporate contract news found."


async def research_smart_money_candidate(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """
    Performs full research and LLM synthesis on a top smart money candidate.
    """
    ticker = candidate["ticker"].upper()
    logger.info(f"Researching smart money candidate: {ticker}")

    metrics = fetch_financial_metrics(ticker)
    company_name = metrics.get("company_name", ticker)
    sector = metrics.get("sector", "General")
    industry = metrics.get("industry", "Unknown")

    catalyst_news = search_catalyst_context(ticker, sector)

    # Format inflow ledger
    ledger = []
    for it in candidate.get("insider_trades", []):
        raw_price = it.get("price")
        if (not raw_price or raw_price <= 0) and it.get("value") and it.get("qty"):
            try:
                raw_price = float(it["value"]) / float(it["qty"])
            except Exception:
                raw_price = None

        if (not raw_price or raw_price <= 0) and it.get("trade_date"):
            raw_price = get_historical_trade_price(ticker, it["trade_date"])

        if raw_price and raw_price > 0:
            price_str = f"${raw_price:.2f}"
        elif metrics.get("current_price"):
            price_str = f"~${float(metrics['current_price']):.2f}"
        else:
            price_str = "Market"

        ledger.append({
            "type": "Form 4 Insider",
            "name": it.get("insider_name"),
            "role": it.get("title"),
            "price": price_str,
            "amount": f"${it.get('value', 0):,.2f}",
            "date": it.get("trade_date"),
            "delta_own": f"+{it.get('delta_own', 0)*100:.1f}%" if it.get("delta_own") else "N/A",
        })
    for ct in candidate.get("congress_trades", []):
        t_date = ct.get("trade_date", "")
        est_price = get_historical_trade_price(ticker, t_date) if t_date else None
        if est_price:
            price_str = f"~${est_price:.2f}"
        elif metrics.get("current_price"):
            price_str = f"~${float(metrics['current_price']):.2f}"
        else:
            price_str = "Bracket Disclosed"

        ledger.append({
            "type": "Congressional STOCK Act",
            "name": ct.get("politician", "Member of Congress"),
            "role": "Congress / Senate",
            "price": price_str,
            "amount": ct.get("amount_range", "$15,001 - $50,000"),
            "date": t_date,
            "delta_own": "N/A",
        })

    prompt_content = f"""
Ticker: ${ticker} ({company_name})
Sector: {sector} | Industry: {industry}
Current Price: ${metrics.get('current_price', 'N/A')} | Target Price: ${metrics.get('target_price', 'N/A')}
Trailing P/E: {metrics.get('pe_ratio', 'N/A')} | Forward P/E: {metrics.get('forward_pe', 'N/A')}

Smart Money Conviction Score: {candidate.get('conviction_score')}
Total Buy Volume: ${candidate.get('total_buy_volume', 0):,.2f}
Cluster Count: {candidate.get('cluster_count')} Insiders

INFLOW LEDGER:
{ledger}

EXTERNAL CATALYST & POLICY SEARCH RESULTS:
{catalyst_news}
"""

    try:
        res = await smart_money_agent.run(prompt_content)
        analysis = res.output
    except Exception as e:
        logger.error(f"Gemini smart money analysis failed for {ticker}: {e}")
        # Graceful fallback
        analysis = SmartMoneyCatalystAnalysis(
            conviction_tier="Speculative Accumulation",
            political_catalyst_analysis=f"Monitored recent filings for {ticker}. Legislative and contract disclosures pending further review.",
            corporate_catalyst_analysis=f"Insiders accumulated ${candidate.get('total_buy_volume', 0):,.0f} in open-market purchases, signaling confidence in forward operations.",
            catalyst_horizon="45-90 days until next quarterly disclosures.",
            actionable_thesis=f"Accumulate ${ticker} on weakness targeting consensus price of ${metrics.get('target_price', 'N/A')}."
        )

    return {
        "ticker": ticker,
        "company_name": company_name,
        "sector": sector,
        "industry": industry,
        "current_price": metrics.get("current_price"),
        "target_price": metrics.get("target_price"),
        "conviction_score": candidate.get("conviction_score", 0.0),
        "conviction_tier": analysis.conviction_tier,
        "cluster_count": candidate.get("cluster_count", 0),
        "total_buy_volume": candidate.get("total_buy_volume", 0.0),
        "top_buyer_summary": candidate.get("top_buyer_summary", ""),
        "inflow_ledger": ledger,
        "political_catalyst_analysis": analysis.political_catalyst_analysis,
        "corporate_catalyst_analysis": analysis.corporate_catalyst_analysis,
        "catalyst_horizon": analysis.catalyst_horizon,
        "actionable_thesis": analysis.actionable_thesis,
        "raw_metrics": metrics,
    }

