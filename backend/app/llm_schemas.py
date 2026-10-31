from pydantic import BaseModel, Field
from typing import Literal

class StockReport(BaseModel):
    community_sentiment: str = Field(description="A summary percentage and feeling of community sentiment on Reddit (e.g. '53% Neutral/Bullish').")
    community_hype: str = Field(description="A summary of the current hype, topics, and narratives discussed on Reddit.")
    
    ground_truth_status: str = Field(description="Factual summary of the company's current position and standing in the industry.")
    ground_truth_filings_news: str = Field(description="Key highlights synthesized from recent SEC filings and financial news.")
    events_happenings: str = Field(description="Key events, product launches, tech advancements, or macroeconomic factors (such as geopolitics or conflicts) that could materially impact the stock price or the industry.")
    
    smart_money_verdict: str = Field(default="Neutral", description="Smart Money Divergence verdict (e.g. 'Bearish Divergence: Insiders Selling into Retail Hype', 'Bullish Accumulation: C-Suite Buying', 'Neutral Flow').")
    insider_activity_summary: str = Field(default="No significant insider activity.", description="Concise synthesis of recent SEC Form 4 insider transactions, executive positions, and Congressional disclosures.")
    
    reconciliation_risk_score: Literal["Low", "Medium", "High"] = Field(description="Assessed risk score by reconciling the community hype vs ground-truth.")
    reconciliation_analysis: str = Field(description="A reconciled analysis showing if Wall Street or Reddit consensus is right, identifying any unpriced reward or risk.")
    reconciliation_actionable_insight: str = Field(description="A concrete, actionable insight or specific metric/date to track next (e.g. upcoming quarterly report segment growth).")
    
    recommendation: Literal["BUY", "SELL", "HOLD"] = Field(description="The final standard recommendation. Default to HOLD.")
    recommendation_rationale: str = Field(description="Brief 1-2 sentence justification for the final recommendation.")

class TrajectoryAnalysis(BaseModel):
    divergence_analysis: str = Field(description="Analysis of divergence or convergence between retail hype/sentiment and actual stock price movements across the historical reports.")
    catalyst_follow_through: str = Field(description="Evaluation of whether previously identified catalysts, actionable insights, and corporate watchpoints played out across subsequent reports.")
    trajectory_outlook: str = Field(description="Longitudinal outlook synthesizing the multi-day trend, consensus stability, and overall risk posture.")
