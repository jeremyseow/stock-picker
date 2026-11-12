from pydantic import BaseModel, Field
from typing import Literal


class CoreIntelSynthesis(BaseModel):
    """Structured fundamental reality check synthesized across filings, financial metrics, and macro news."""
    ground_truth_status: str = Field(description="Factual summary of the company's current position, moat, and industry standing.")
    ground_truth_filings_news: str = Field(description="Key highlights synthesized from recent SEC 10-Q/8-K filings and financial reports.")
    events_happenings: str = Field(description="Key upcoming events, product launches, tech advancements, or macro/geopolitical factors.")
    risk_score: Literal["Low", "Medium", "High"] = Field(description="Assessed fundamental risk score based on balance sheet, competition, and valuation.")
    risk_analysis: str = Field(description="Concise analysis justifying the fundamental risk score.")
    actionable_insight: str = Field(description="A concrete, trackable operational metric, catalyst date, or quarterly earnings milestone to watch.")


class RetailOverlayAnalysis(BaseModel):
    """Engine 1 retail sentiment overlay synthesized strictly from Reddit discussion threads and Core Intel."""
    community_sentiment: str = Field(description="A summary percentage and feeling of community sentiment on Reddit (e.g. '75% Bullish').")
    community_hype: str = Field(description="A summary of the current retail hype, topics, and speculative narratives discussed on Reddit.")
    reconciliation_actionable_insight: str = Field(description="A concrete, actionable insight or specific metric/catalyst to watch next based on retail hype vs Core Intel fundamentals.")
    recommendation: Literal["BUY", "SELL", "HOLD"] = Field(default="HOLD", description="Conservative recommendation. Default to HOLD unless unambiguous evidence justifies BUY or SELL.")
    recommendation_rationale: str = Field(description="Brief 1-2 sentence justification for the final recommendation.")


class TrajectoryAnalysis(BaseModel):
    divergence_analysis: str = Field(description="Analysis of divergence or convergence between retail hype/sentiment and actual stock price movements across the historical reports.")
    catalyst_follow_through: str = Field(description="Evaluation of whether previously identified catalysts, actionable insights, and corporate watchpoints played out across subsequent reports.")
    trajectory_outlook: str = Field(description="Longitudinal outlook synthesizing the multi-day trend, consensus stability, and overall risk posture.")


class SmartMoneyCatalystAnalysis(BaseModel):
    conviction_tier: Literal["High Conviction Catalyst Buy", "Speculative Accumulation", "Moderate Cluster"] = Field(
        description="Assessed tier based on buyer seniority, cluster size, and policy alignment."
    )
    political_catalyst_analysis: str = Field(
        description="Analysis of relevant legislative bills, government subsidies, committee oversight, or geopolitical developments related to the buyers."
    )
    corporate_catalyst_analysis: str = Field(
        description="Analysis of corporate turnaround signals, earnings catalysts, contract awards, or valuation discrepancies prompting insider buying."
    )
    catalyst_horizon: str = Field(
        description="Projected timeline for catalyst realization (e.g. '30-60 days ahead of Q4 earnings & defense markup')."
    )
    actionable_thesis: str = Field(
        description="Clear, actionable swing trade thesis detailing entry rationale and primary risk factors."
    )
