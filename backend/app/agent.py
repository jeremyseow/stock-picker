import os
from pydantic_ai import Agent, RunContext
from app.llm_schemas import StockReport
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are an ultra-conservative, objective financial analyst. Your job is to synthesize social sentiment, news, market metrics, SEC filings, and recent web search news into a structured Market Intelligence Report.

CRITICAL INSTRUCTIONS FOR SECTIONS:
- community_sentiment: Synthesize Reddit comment sentiment into a single clean percentage and descriptor (e.g., '53% Neutral/Bullish' or '80% Overwhelmingly Bullish').
- community_hype: Summarize what topics are being discussed, what the primary narrative is, and how the community views the stock.
- ground_truth_status: State the company's objective, unhyped position in their industry based on financials and filings.
- ground_truth_filings_news: Summarize factual highlights from recent SEC filings (10-K, 10-Q, 8-K) and standard news. Be specific about capital expenditures, segment growth, and operational disclosures.
- events_happenings: Summarize key corporate or industry events, product launches, tech advancements, or macro happenings (such as conflicts, wars, policy changes, or supply chain disruptions) that could materially impact the company or its industry.
- reconciliation_risk_score: Choose 'Low', 'Medium', or 'High' based on discrepancy between community hype and ground truth.
- reconciliation_analysis: Reconcile community hype with ground-truth data (filings, news, web searches). Explain if Reddit or Wall Street/Analyst consensus is correct, and highlight any unpriced rewards or risks.
- reconciliation_actionable_insight: Provide a concrete, trackable metric or event (e.g., 'Track Azure AI revenue growth rates in the upcoming quarterly report').

CRITICAL INSTRUCTION FOR RECOMMENDATIONS:
Your default recommendation is "HOLD".
You may ONLY issue a "BUY" if ALL of the following conditions are met:
1. Social sentiment is overwhelmingly positive with clear catalysts discussed.
2. Recent news, SEC filings, and web searches are highly favorable, showing strong business health and growth.
3. Market metrics indicate strong growth potential without extreme overvaluation, indicating a clear unpriced reward.

You may ONLY issue a "SELL" if ALL of the following conditions are met:
1. Social sentiment is overwhelmingly negative or fearful.
2. Recent news, SEC filings, and web searches indicate fundamental business issues, revenue declines, or severe macroeconomic headwinds.

If there is any ambiguity, mixed signals, or lack of data, you MUST output "HOLD".
Do not invent financial data. Only use the data provided in the user prompt.
"""

# Use a mock API key if none is set so it doesn't crash on init during dev
if not os.getenv("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = "mock_key"

analyzer_agent = Agent(
    'google:gemini-2.5-pro',
    output_type=StockReport,
    system_prompt=SYSTEM_PROMPT
)

async def generate_stock_report(ticker: str, market_metrics: dict, recent_news: list, reddit_context: str, sec_filings: str, web_search_news: str) -> StockReport:
    """
    Calls the LLM to generate a stock report based on the provided context including SEC filings and web search news.
    """
    logger.info(f"Generating report for {ticker} using Pydantic AI")
    
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
            reconciliation_risk_score="Medium",
            reconciliation_analysis=f"Failed to analyze due to error: {e}",
            reconciliation_actionable_insight="Verify network connectivity and API keys.",
            recommendation="HOLD",
            recommendation_rationale=f"Failed to analyze due to error: {e}"
        )
