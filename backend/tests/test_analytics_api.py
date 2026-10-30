import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database import Base, get_db
from app.models import TickerReport, TickerTrajectoryAnalysis
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def test_db():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async with async_session() as session:
        # Seed test data
        r1 = TickerReport(
            ticker="AAPL",
            date=datetime(2026, 10, 28, 12, 0, 0, tzinfo=timezone.utc),
            current_price=220.0,
            target_price=240.0,
            community_sentiment="60% Bullish",
            community_hype="iPhone 18 rumors",
            ground_truth_status="Solid hardware margins",
            ground_truth_filings_news="10-Q showed strong services growth",
            events_happenings="New product launch scheduled",
            reconciliation_risk_score="Low",
            reconciliation_analysis="Consensus aligns with retail sentiment",
            reconciliation_actionable_insight="Track Q4 services revenue",
            recommendation="BUY",
            recommendation_rationale="Services growth offset hardware maturity",
            raw_metrics={"industry": "Consumer Electronics", "sector": "Technology", "pe_ratio": 30.5}
        )
        r2 = TickerReport(
            ticker="AAPL",
            date=datetime(2026, 10, 29, 12, 0, 0, tzinfo=timezone.utc),
            current_price=225.0,
            target_price=245.0,
            community_sentiment="75% Bullish",
            community_hype="Services revenue explosion",
            ground_truth_status="Services reached all time high",
            ground_truth_filings_news="8-K update on international market",
            events_happenings="Retail store expansion in Asia",
            reconciliation_risk_score="Low",
            reconciliation_analysis="Momentum building sustainably",
            reconciliation_actionable_insight="Monitor gross margin stability",
            recommendation="BUY",
            recommendation_rationale="Services beat consensus",
            raw_metrics={"industry": "Consumer Electronics", "sector": "Technology", "pe_ratio": 31.0}
        )
        r3 = TickerReport(
            ticker="NVDA",
            date=datetime(2026, 10, 29, 12, 0, 0, tzinfo=timezone.utc),
            current_price=130.0,
            target_price=150.0,
            community_sentiment="85% Bullish",
            community_hype="AI GPU demand soaring",
            ground_truth_status="Data center monopoly",
            ground_truth_filings_news="10-Q confirmed backlog",
            events_happenings="New architecture revealed",
            reconciliation_risk_score="Medium",
            reconciliation_analysis="Priced for perfection",
            reconciliation_actionable_insight="Track Blackwell shipments",
            recommendation="HOLD",
            recommendation_rationale="High valuation warrants holding",
            raw_metrics={"industry": "Semiconductors", "sector": "Technology", "pe_ratio": 55.0}
        )
        r4 = TickerReport(
            ticker="GOOG",
            date=datetime(2026, 10, 29, 12, 0, 0, tzinfo=timezone.utc),
            current_price=280.0,
            target_price=350.0,
            community_sentiment="70% Bullish",
            community_hype="Cloud TPU and Gemini momentum",
            ground_truth_status="Dominant search and cloud growth",
            ground_truth_filings_news="10-Q confirmed strong cloud margins",
            events_happenings="Gemini 3 launch",
            reconciliation_risk_score="Low",
            reconciliation_analysis="Fundamentals strong",
            reconciliation_actionable_insight="Monitor advertising growth",
            recommendation="BUY",
            recommendation_rationale="Search moats intact",
            raw_metrics={"industry": "Internet", "sector": "Technology", "pe_ratio": 24.0}
        )
        session.add_all([r1, r2, r3, r4])
        await session.commit()
        
    async def override_get_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    await engine.dispose()

@pytest.mark.asyncio
async def test_get_report_dates(test_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/reports/dates")
        assert res.status_code == 200
        dates = res.json()
        assert dates == ["2026-10-29", "2026-10-28"]

@pytest.mark.asyncio
async def test_get_reports_by_date(test_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Specific date
        res = await client.get("/api/reports?date=2026-10-29")
        assert res.status_code == 200
        reports = res.json()
        assert len(reports) == 3
        tickers = [r["ticker"] for r in reports]
        assert "AAPL" in tickers
        assert "NVDA" in tickers
        assert "GOOG" in tickers
        
        # Default latest date
        res_latest = await client.get("/api/reports")
        assert res_latest.status_code == 200
        assert len(res_latest.json()) == 3

@pytest.mark.asyncio
async def test_get_analytics_tickers(test_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/analytics/tickers")
        assert res.status_code == 200
        tickers = res.json()
        assert tickers == ["AAPL", "GOOG", "NVDA"]

@pytest.mark.asyncio
async def test_get_ticker_analytics(test_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Existing ticker
        res = await client.get("/api/analytics/ticker/AAPL")
        assert res.status_code == 200
        history = res.json()
        assert len(history) == 2
        assert history[0]["current_price"] == 220.0
        assert history[1]["current_price"] == 225.0

        # Alias resolution: requesting GOOGL should resolve to GOOG
        res_alias = await client.get("/api/analytics/ticker/GOOGL")
        assert res_alias.status_code == 200
        goog_history = res_alias.json()
        assert len(goog_history) == 1
        assert goog_history[0]["ticker"] == "GOOG"

        # Report alias resolution: requesting /api/reports/GOOGL should return GOOG report
        res_rep_alias = await client.get("/api/reports/GOOGL")
        assert res_rep_alias.status_code == 200
        assert res_rep_alias.json()["ticker"] == "GOOG"

        # Non-existing ticker
        res_404 = await client.get("/api/analytics/ticker/XYZ")
        assert res_404.status_code == 404

def test_ticker_extractor_alias():
    from app.ticker_extractor import extract_tickers_from_text
    # Both $GOOGL and raw GOOGL should map to GOOG
    extracted = extract_tickers_from_text("Look at $GOOGL and GOOGL vs $NVDA")
    assert "GOOGL" not in extracted
    assert "GOOG" in extracted
    assert "NVDA" in extracted

@pytest.mark.asyncio
async def test_ticker_meta_analysis_endpoints(test_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # GET meta-analysis when uncached
        res_get = await client.get("/api/analytics/ticker/AAPL/meta-analysis")
        assert res_get.status_code == 200
        data = res_get.json()
        assert data["cached"] is False
        assert data["can_generate"] is True
        assert data["report_count"] == 2

        # NVDA only has 1 report -> cannot generate
        res_nvda_post = await client.post("/api/analytics/ticker/NVDA/meta-analysis")
        assert res_nvda_post.status_code == 400
        assert "At least 2 historical reports" in res_nvda_post.json()["detail"]

