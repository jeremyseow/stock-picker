import os
from pydantic_ai import Agent, RunContext
from app.llm_schemas import StockReport, TrajectoryAnalysis
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are an ultra-conservative, objective financial analyst. Your job is to synthesize social sentiment, news, market metrics, SEC filings, recent web search news, and SEC Form 4 insider/Congressional trading disclosures into a structured Market Intelligence Report.

CRITICAL INSTRUCTIONS FOR SECTIONS:
- community_sentiment: Synthesize Reddit comment sentiment into a single clean percentage and descriptor (e.g., '53% Neutral/Bullish' or '80% Overwhelmingly Bullish').
- community_hype: Summarize what topics are being discussed, what the primary narrative is, and how the community views the stock.
- ground_truth_status: State the company's objective, unhyped position in their industry based on financials and filings.
- ground_truth_filings_news: Summarize factual highlights from recent SEC filings (10-K, 10-Q, 8-K) and standard news. Be specific about capital expenditures, segment growth, and operational disclosures.
- events_happenings: Summarize key corporate or industry events, product launches, tech advancements, or macro happenings (such as conflicts, wars, policy changes, or supply chain disruptions) that could materially impact the company or its industry.
- smart_money_verdict: Provide a concise diagnosis of Smart Money vs. Retail alignment (e.g., 'Bearish Divergence: C-Suite Selling', 'Bullish Insider Accumulation', 'Neutral Insider Flow', or 'No Form 4 Activity'). CRITICAL: If SEC Form 4 insider data is unavailable or has_data is False, you MUST NOT claim 'C-Suite Selling' or 'C-Suite Accumulation'. In that case, output 'No Form 4 Activity' (or 'No Form 4 Filings / Congressional Selling' if only Congressional trades exist).
- insider_activity_summary: Synthesize SEC Form 4 insider buying/selling volume, net shares, key executive transactions (CEOs/CFOs/Directors), and any Congressional/politician trade disclosures. Explain if insiders are accumulating or dumping into retail hype.
- reconciliation_risk_score: Choose 'Low', 'Medium', or 'High' based on discrepancy between community hype, ground truth, and insider trading flows.
- reconciliation_analysis: Reconcile community hype with ground-truth data (filings, news, web searches, and insider selling). Explain if Reddit or Wall Street/Analyst consensus is correct, and highlight any unpriced rewards or risks.
- reconciliation_actionable_insight: Provide a concrete, trackable metric or event (e.g., 'Track Azure AI revenue growth rates in the upcoming quarterly report').

CRITICAL INSTRUCTION FOR RECOMMENDATIONS:
Your default recommendation is "HOLD".
You may ONLY issue a "BUY" if ALL of the following conditions are met:
1. Social sentiment is overwhelmingly positive with clear catalysts discussed.
2. Recent news, SEC filings, and web searches are highly favorable, showing strong business health and growth.
3. Market metrics indicate strong growth potential without extreme overvaluation, indicating a clear unpriced reward.
4. SEC Form 4 disclosures DO NOT show heavy net insider selling or aggressive C-suite liquidation into the rally. If corporate insiders are heavily selling shares, you MUST NOT issue a BUY.

You may ONLY issue a "SELL" if ALL of the following conditions are met:
1. Social sentiment is overwhelmingly negative or fearful, OR insiders are aggressively liquidating while fundamentals deteriorate.
2. Recent news, SEC filings, and web searches indicate fundamental business issues, revenue declines, or severe macroeconomic headwinds.

If there is any ambiguity, mixed signals, or lack of data, you MUST output "HOLD".
Do not invent financial data. Only use the data provided in the user prompt.
"""

TRAJECTORY_SYSTEM_PROMPT = """
You are a senior quantitative and fundamental equity analyst specializing in longitudinal meta-analysis.
Your task is to analyze chronological historical intelligence reports for a single stock ticker across multiple pipeline runs.

CRITICAL INSTRUCTIONS FOR SECTIONS:
- divergence_analysis: Analyze whether retail sentiment/hype on Reddit diverged or converged with the stock's actual market price and analyst target price over time. Highlight whether retail hype spiked into resistance, whether sentiment soured near a bottom, or whether price action validated sentiment.
- catalyst_follow_through: Evaluate whether previous watchpoints, SEC filing disclosures, actionable insights, or catalysts mentioned in earlier reports actually materialized in subsequent reports.
- trajectory_outlook: Provide a comprehensive longitudinal outlook on whether the company's fundamentals and risk posture are improving, stable, or deteriorating over time. Summarize the stability of the recommendation posture and identify the primary pivot factor for future runs.

Base your analysis STRICTLY on the historical report snapshots provided in the prompt. Do not hallucinate external dates or unverified numbers.
"""

# Use a mock API key if none is set so it doesn't crash on init during dev
if not os.getenv("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = "mock_key"

analyzer_agent = Agent(
    'google:gemini-4-argon',
    output_type=StockReport,
    system_prompt=SYSTEM_PROMPT
)

trajectory_agent = Agent(
    'google:gemini-4-argon',
    output_type=TrajectoryAnalysis,
    system_prompt=TRAJECTORY_SYSTEM_PROMPT
)

async def generate_stock_report(
    ticker: str,
    market_metrics: dict,
    recent_news: list,
    reddit_context: str,
    sec_filings: str,
    web_search_news: str,
    insider_data: dict | None = None,
    congressional_trades: list | None = None
) -> StockReport:
    """
    Calls the LLM to generate a stock report based on the provided context including SEC filings,
    web search news, SEC Form 4 insider transactions, and Congressional disclosures.
    """
    logger.info(f"Generating report for {ticker} using Pydantic AI")
    
    insider_text = "No SEC Form 4 insider transaction filings recorded for this ticker (has_data: False)."
    if insider_data and insider_data.get("has_data"):
        txs = insider_data.get("recent_transactions", [])
        tx_lines = [
            f"- {tx['date']} | {tx['insider']} ({tx['position']}) | {tx['type']} {tx['shares']:,} shares (~${tx['value']:,}) | {tx['text']}"
            for tx in txs[:5]
        ]
        insider_text = f"""
- Sentiment: {insider_data.get('sentiment_label')}
- Purchases (6m): {insider_data.get('purchases_shares'):,.0f} shares ({insider_data.get('purchases_trans')} transactions)
- Sales (6m): {insider_data.get('sales_shares'):,.0f} shares ({insider_data.get('sales_trans')} transactions)
- Net Shares (6m): {insider_data.get('net_shares'):,.0f} shares
- Recent Form 4 Filings:
""" + "\n".join(tx_lines)

    congressional_text = "No recent Congressional trading reports found."
    if congressional_trades:
        congressional_text = "\n".join([
            f"- {c.get('title')} ({c.get('link')}): {c.get('snippet')}"
            for c in congressional_trades
        ])

    prompt = f"""
    Analyze the following data for {ticker}:
    
    === MARKET METRICS ===
    {market_metrics}
    
    === RECENT NEWS ===
    {recent_news}
    
    === SEC FILINGS ===
    {sec_filings}
    
    === WEB SEARCH NEWS ===
    {web_search_news}
    
    === SMART MONEY & INSIDER TRADING (SEC FORM 4) ===
    {insider_text}
    
    === CONGRESSIONAL & SENATE DISCLOSURES ===
    {congressional_text}
    
    === REDDIT CONTEXT ===
    {reddit_context}
    """
    
    try:
            
        result = await analyzer_agent.run(prompt)
        return result.output
    except Exception as e:
        logger.error(f"Error generating report for {ticker}: {e}")
        # Return a fallback HOLD report
        return StockReport(
            community_sentiment="Error",
            community_hype="Error fetching data.",
            ground_truth_status="Error fetching data.",
            ground_truth_filings_news="Error fetching data.",
            events_happenings="Error fetching data.",
            smart_money_verdict="Error fetching data.",
            insider_activity_summary="Error fetching data.",
            reconciliation_risk_score="Medium",
            reconciliation_analysis=f"Failed to analyze due to error: {e}",
            reconciliation_actionable_insight="Verify network connectivity and API keys.",
            recommendation="HOLD",
            recommendation_rationale=f"Failed to analyze due to error: {e}"
        )

async def generate_trajectory_analysis(ticker: str, historical_reports: list[dict]) -> TrajectoryAnalysis:
    """
    Calls the LLM to synthesize multi-run historical reports into a trajectory meta-analysis.
    """
    logger.info(f"Generating trajectory analysis for {ticker} across {len(historical_reports)} historical reports")
    
    formatted_history = []
    for idx, rep in enumerate(historical_reports, 1):
        formatted_history.append(f"""
--- REPORT RUN #{idx} ({rep.get('date')}) ---
- Market Price: ${rep.get('current_price')} | Target Price: ${rep.get('target_price')}
- Recommendation: {rep.get('recommendation')} ({rep.get('recommendation_rationale')})
- Sentiment: {rep.get('community_sentiment')} | Hype: {rep.get('community_hype')}
- Risk Score: {rep.get('reconciliation_risk_score')}
- Ground Truth: {rep.get('ground_truth_status')}
- Actionable Insight from this run: {rep.get('reconciliation_actionable_insight')}
""")
    
    history_text = "\n".join(formatted_history)
    prompt = f"""
    Analyze the following chronological historical intelligence reports for {ticker}:

    {history_text}

    Synthesize the longitudinal trajectory, divergence between retail sentiment and market price, and follow-through on previous actionable insights.
    """

    try:
        result = await trajectory_agent.run(prompt)
        return result.output
    except Exception as e:
        logger.error(f"Error generating trajectory analysis for {ticker}: {e}")
        return TrajectoryAnalysis(
            divergence_analysis=f"Unable to generate divergence analysis: {e}",
            catalyst_follow_through=f"Unable to evaluate catalyst follow-through: {e}",
            trajectory_outlook=f"Unable to generate trajectory outlook: {e}"
        )
