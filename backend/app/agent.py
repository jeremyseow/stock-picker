import os
from pydantic_ai import Agent
from app.llm_schemas import RetailOverlayAnalysis, TrajectoryAnalysis
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are an ultra-conservative, objective financial analyst specializing in Engine 1 (Retail Social Sentiment & Narrative Overlay).
Your job is to synthesize Reddit discussion sentiment against Core Equity Intelligence fundamentals into a structured Retail Sentiment Overlay.

CRITICAL INSTRUCTIONS FOR SECTIONS:
- community_sentiment: Synthesize Reddit comment sentiment into a single clean percentage and descriptor (e.g., '53% Neutral/Bullish' or '80% Overwhelmingly Bullish').
- community_hype: Summarize what topics are being discussed, what the primary narrative is, and how the retail community views the stock.
- reconciliation_actionable_insight: Provide a concrete, trackable metric or catalyst reconciling retail expectations with fundamental reality (e.g., 'Track Azure AI revenue growth rates in the upcoming quarterly report').

CRITICAL INSTRUCTION FOR RECOMMENDATIONS:
Your default recommendation is "HOLD".
You may ONLY issue a "BUY" if ALL of the following conditions are met:
1. Social sentiment is overwhelmingly positive with clear catalysts discussed.
2. Recent news, SEC filings, and Core Intel fundamentals confirm strong business health and growth.
3. Market metrics indicate strong growth potential without extreme overvaluation, indicating a clear unpriced reward.

You may ONLY issue a "SELL" if ALL of the following conditions are met:
1. Social sentiment is overwhelmingly negative or fearful while fundamentals deteriorate.
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
    output_type=RetailOverlayAnalysis,
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
    core_intel_summary: str = "",
) -> RetailOverlayAnalysis:
    """
    Calls the LLM to generate Engine 1's pure Retail Sentiment Overlay based on Reddit social discussions
    grounded by Core Equity Intelligence metrics, SEC filings, and news.
    """
    logger.info(f"Generating Engine 1 Retail Overlay report for {ticker} using Pydantic AI")

    prompt = f"""
    Analyze the following data for {ticker}:

    === CORE EQUITY INTEL SUMMARY ===
    {core_intel_summary or 'Evaluate against raw market metrics and SEC filings below.'}

    === MARKET METRICS ===
    {market_metrics}

    === RECENT NEWS ===
    {recent_news}

    === SEC FILINGS ===
    {sec_filings}

    === WEB SEARCH NEWS ===
    {web_search_news}

    === REDDIT CONTEXT ===
    {reddit_context}
    """

    try:
        result = await analyzer_agent.run(prompt)
        return result.output
    except Exception as e:
        logger.error(f"Error generating Engine 1 retail overlay for {ticker}: {e}")
        return RetailOverlayAnalysis(
            community_sentiment="Error",
            community_hype="Error fetching data.",
            reconciliation_actionable_insight="Verify network connectivity and API keys.",
            recommendation="HOLD",
            recommendation_rationale=f"Failed to analyze due to error: {e}",
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
