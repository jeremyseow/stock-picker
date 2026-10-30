from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from datetime import datetime, timezone
from app.database import Base

class DailyTicker(Base):
    __tablename__ = "daily_tickers"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    ticker = Column(String, index=True)
    rank = Column(Integer)
    mention_count = Column(Integer)
    engagement_score = Column(Float)
    
class TickerReport(Base):
    __tablename__ = "ticker_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    current_price = Column(Float)
    target_price = Column(Float)
    
    community_sentiment = Column(String)
    community_hype = Column(String)
    
    ground_truth_status = Column(String)
    ground_truth_filings_news = Column(String)
    events_happenings = Column(String)
    
    reconciliation_risk_score = Column(String)
    reconciliation_analysis = Column(String)
    reconciliation_actionable_insight = Column(String)
    
    recommendation = Column(String) # BUY, SELL, HOLD
    recommendation_rationale = Column(String)
    raw_metrics = Column(JSON)
    raw_news = Column(JSON)

class TickerTrajectoryAnalysis(Base):
    __tablename__ = "ticker_trajectory_analyses"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    latest_report_id = Column(Integer, index=True)
    report_count = Column(Integer)
    divergence_analysis = Column(String)
    catalyst_follow_through = Column(String)
    trajectory_outlook = Column(String)
