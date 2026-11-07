import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database import Base, get_db
from app.models import (
    CoreEquityReport,
    DailyTicker,
    RetailSentimentReport,
    SmartMoneyTicker,
    SmartMoneyReport,
    SynthesisReport,
)
from app.core_intel_engine import research_core_equity_intel
from app.llm_schemas import CoreIntelSynthesis
from app.crud import get_latest_synthesis_reports
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def test_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def app_client():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async def override_get_db():
        async with async_session() as session:
            yield session
            
    app.dependency_overrides[get_db] = override_get_db

    now = datetime(2026, 11, 1, 12, 0, 0, tzinfo=timezone.utc)
    yesterday = datetime(2026, 10, 31, 12, 0, 0, tzinfo=timezone.utc)

    # Seed test data across all tables
    async with async_session() as session:
        # Core Intel
        c1 = CoreEquityReport(
            ticker="PLTR",
            date=now,
            company_name="Palantir Technologies Inc.",
            sector="Technology",
            industry="Software - Infrastructure",
            current_price=42.50,
            target_price=50.00,
            ground_truth_status="Expanding government and commercial AI contracts",
            ground_truth_filings_news="Q3 10-Q showed 44% US commercial revenue growth",
            events_happenings="AIP bootcamps accelerating enterprise conversions",
            risk_score="Medium",
            risk_analysis="High valuation multiple and potential government budget cycles",
            actionable_insight="Track commercial revenue expansion",
            raw_metrics={"pe_ratio": 85.2, "forward_pe": 60.1, "fifty_two_week_high": 45.0, "fifty_two_week_low": 15.0, "market_cap": 95000000000.0}
        )
        session.add(c1)
        await session.flush()

        # Retail report
        dt1 = DailyTicker(ticker="PLTR", mention_count=120, rank=1, engagement_score=100.0, date=now)
        session.add(dt1)
        await session.flush()

        rr1 = RetailSentimentReport(
            ticker="PLTR",
            date=now,
            rank=1,
            mention_count=120,
            engagement_score=100.0,
            core_intel_id=c1.id,
            community_sentiment="85% Bullish",
            community_hype="AIP enterprise dominance buzz",
            recommendation="BUY",
            recommendation_rationale="Commercial momentum outpaces valuation headwind"
        )
        # Yesterday retail report (for date filter testing)
        rr0 = RetailSentimentReport(
            ticker="PLTR",
            date=yesterday,
            rank=2,
            mention_count=15,
            engagement_score=20.0,
            core_intel_id=c1.id,
            community_sentiment="50% Neutral",
            community_hype="Early social mentions",
            recommendation="HOLD",
            recommendation_rationale="Early accumulation phase"
        )
        session.add_all([rr1, rr0])

        # Smart money report
        smt1 = SmartMoneyTicker(
            ticker="PLTR",
            date=now,
            rank=1,
            conviction_score=88.5,
            insider_score=50.0,
            political_score=38.5,
            cluster_count=3,
            total_buy_volume=12500000.0,
            top_buyer_summary="Multiple board directors purchased shares post-earnings"
        )
        session.add(smt1)
        await session.flush()

        smr1 = SmartMoneyReport(
            ticker="PLTR",
            date=now,
            core_intel_id=c1.id,
            conviction_tier="Tier-1 Alpha",
            cluster_count=3,
            total_buy_volume=12500000.0,
            top_buyer_summary="Multiple board directors purchased shares post-earnings",
            inflow_ledger=[
                {"buyer": "Director Alex", "type": "Insider", "volume": 5000000, "date": "2026-10-25"}
            ],
            political_catalyst_analysis="Defense department procurement budget increase",
            corporate_catalyst_analysis="Operating margin expansion",
            catalyst_horizon="1-3 Months",
            actionable_thesis="Follow institutional cluster ahead of contract cycle"
        )
        # Yesterday smart money report (for date filter testing)
        smr0 = SmartMoneyReport(
            ticker="PLTR",
            date=yesterday,
            core_intel_id=c1.id,
            conviction_tier="Moderate Cluster",
            cluster_count=1,
            total_buy_volume=2000000.0,
            top_buyer_summary="Single director purchase",
            inflow_ledger=[],
            catalyst_horizon="6 Months",
            actionable_thesis="Preliminary accumulation"
        )
        session.add_all([smr1, smr0])

        # Smart-Money only ticker without retail report (e.g. ACN)
        c_acn = CoreEquityReport(
            ticker="ACN",
            date=now,
            company_name="Accenture plc",
            sector="Technology",
            industry="IT Services",
            current_price=285.00,
            target_price=330.00,
            ground_truth_status="Strong enterprise cloud consulting backlog",
            risk_score="Low",
            actionable_insight="Track federal AI contracts",
            raw_metrics={"pe_ratio": 24.5, "forward_pe": 21.0}
        )
        session.add(c_acn)
        await session.flush()

        smr_acn = SmartMoneyReport(
            ticker="ACN",
            date=now,
            core_intel_id=c_acn.id,
            conviction_tier="Tier-1 Alpha",
            cluster_count=2,
            total_buy_volume=8000000.0,
            top_buyer_summary="CFO and VP purchase shares",
            inflow_ledger=[],
            actionable_thesis="Institutional cluster inflow in consulting"
        )
        session.add(smr_acn)

        # Synthesis Record for now
        sr1 = SynthesisReport(
            ticker="PLTR",
            date=now,
            core_intel_id=c1.id,
            archetype="The Rocket",
            retail_awareness_level="Mainstream Momentum",
            timing_edge_score=8.7,
            retail_mentions=120,
            smart_money_conviction=88.5,
            smart_money_flow="Tier-1 Alpha",
            synthesis_diagnosis="Dual engine confirmation: heavy institutional cluster aligning with strong retail momentum.",
            recommended_action="AGGRESSIVE BUY"
        )
        # Duplicate record from second run on same date (to verify deduplication)
        sr1_dup = SynthesisReport(
            ticker="PLTR",
            date=now + timedelta(minutes=5),
            core_intel_id=c1.id,
            archetype="The Rocket",
            retail_awareness_level="Mainstream Momentum",
            timing_edge_score=8.9,
            retail_mentions=125,
            smart_money_conviction=88.5,
            smart_money_flow="Tier-1 Alpha",
            synthesis_diagnosis="Dual engine confirmation: latest run.",
            recommended_action="AGGRESSIVE BUY"
        )
        # Yesterday synthesis record (for archetype progression)
        sr0 = SynthesisReport(
            ticker="PLTR",
            date=yesterday,
            core_intel_id=None,
            archetype="Silent Accumulation",
            retail_awareness_level="Zero Awareness (Stealth)",
            timing_edge_score=9.4,
            retail_mentions=5,
            smart_money_conviction=80.0,
            smart_money_flow="Tier-1 Alpha",
            synthesis_diagnosis="Early accumulation detected before retail noticed.",
            recommended_action="BUY"
        )
        session.add_all([sr1, sr1_dup, sr0])
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_core_intel_caching(test_session: AsyncSession):
    """Verify research_core_equity_intel caches results within 6 hours without redundant LLM calls."""
    mock_metrics = {
        "current_price": 100.0,
        "target_price": 120.0,
        "market_cap": 1000000000.0,
        "pe_ratio": 20.0,
        "forward_pe": 18.0,
        "sector": "Industrials",
        "industry": "Aerospace",
        "company_name": "Test Aero Inc.",
    }
    mock_synthesis = CoreIntelSynthesis(
        ground_truth_status="Solid aerospace order book",
        ground_truth_filings_news="10-Q showed record backlog",
        events_happenings="New defense contract awarded",
        risk_score="Low",
        risk_analysis="Supply chain raw materials delay",
        actionable_insight="Track deliveries next quarter",
    )
    mock_agent_result = MagicMock()
    mock_agent_result.output = mock_synthesis

    with patch("app.core_intel_engine.fetch_financial_metrics", return_value=mock_metrics), \
         patch("app.core_intel_engine.fetch_sec_filings", return_value=[]), \
         patch("app.core_intel_engine.fetch_recent_news", return_value=[]), \
         patch("app.core_intel_engine.fetch_web_search_news", return_value=[]), \
         patch("app.core_intel_engine.core_intel_agent.run", new_callable=AsyncMock) as mock_agent_run:
        
        mock_agent_run.return_value = mock_agent_result

        # Call 1: should invoke LLM agent and create record
        intel_1 = await research_core_equity_intel("AERO", db=test_session)
        assert intel_1 is not None
        assert intel_1["ticker"] == "AERO"
        assert intel_1["current_price"] == 100.0
        assert mock_agent_run.call_count == 1

        # Call 2: within 6 hours, should hit cache and NOT invoke LLM again
        intel_2 = await research_core_equity_intel("AERO", db=test_session)
        assert intel_2 is not None
        assert intel_2["id"] == intel_1["id"]
        assert mock_agent_run.call_count == 1  # Still 1!


@pytest.mark.asyncio
async def test_synthesis_deduplication(test_session: AsyncSession):
    """Verify get_latest_synthesis_reports returns exactly 1 deduplicated record per ticker."""
    now = datetime(2026, 11, 1, 12, 0, 0, tzinfo=timezone.utc)
    records = [
        SynthesisReport(
            ticker="AAPL",
            date=now,
            archetype="Market Noise",
            timing_edge_score=4.0,
            retail_awareness_level="Mainstream Momentum",
            retail_mentions=50,
            smart_money_conviction=0.0,
            smart_money_flow="None",
            synthesis_diagnosis="Run 1",
            recommended_action="PASS"
        ),
        SynthesisReport(
            ticker="AAPL",
            date=now + timedelta(seconds=2),
            archetype="Market Noise",
            timing_edge_score=4.2,
            retail_awareness_level="Mainstream Momentum",
            retail_mentions=52,
            smart_money_conviction=0.0,
            smart_money_flow="None",
            synthesis_diagnosis="Run 2",
            recommended_action="PASS"
        ),
        SynthesisReport(
            ticker="NVDA",
            date=now + timedelta(seconds=2),
            archetype="The Rocket",
            timing_edge_score=9.0,
            retail_awareness_level="Mainstream Momentum",
            retail_mentions=200,
            smart_money_conviction=85.0,
            smart_money_flow="Tier-1 Alpha",
            synthesis_diagnosis="Run 1",
            recommended_action="BUY"
        )
    ]
    test_session.add_all(records)
    await test_session.commit()

    deduped = await get_latest_synthesis_reports(test_session)
    tickers = [r.ticker for r in deduped]
    assert len(tickers) == len(set(tickers))
    assert "AAPL" in tickers
    assert "NVDA" in tickers
    # NVDA timing_edge_score 9.0 should come before AAPL 4.2
    assert tickers[0] == "NVDA"


@pytest.mark.asyncio
async def test_api_dates_aggregation(app_client: AsyncClient):
    """Verify GET /api/dates aggregates distinct dates across all three datasets."""
    res = await app_client.get("/api/dates")
    assert res.status_code == 200
    dates = res.json()
    assert isinstance(dates, list)
    assert "2026-11-01" in dates
    assert "2026-10-31" in dates


@pytest.mark.asyncio
async def test_api_historical_smart_money_reports(app_client: AsyncClient):
    """Verify GET /api/smart-money/reports?date=YYYY-MM-DD returns filtered smart money records."""
    res = await app_client.get("/api/smart-money/reports?date=2026-11-01")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["ticker"] == "PLTR"
    assert data[0]["conviction_tier"] == "Tier-1 Alpha"

    # Non-existent date
    empty_res = await app_client.get("/api/smart-money/reports?date=2020-01-01")
    assert empty_res.status_code == 200
    assert empty_res.json() == []


@pytest.mark.asyncio
async def test_api_historical_synthesis_reports(app_client: AsyncClient):
    """Verify GET /api/synthesis/reports?date=YYYY-MM-DD returns deduplicated synthesis records."""
    res = await app_client.get("/api/synthesis/reports?date=2026-11-01")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    # PLTR was inserted twice on 2026-11-01, but the endpoint must return only 1 deduplicated record
    tickers = [r["ticker"] for r in data]
    assert tickers.count("PLTR") == 1
    assert data[0]["archetype"] == "The Rocket"


@pytest.mark.asyncio
async def test_api_unified_master_report(app_client: AsyncClient):
    """Verify GET /api/master/report/{ticker} returns the complete Unified Master Report payload."""
    res = await app_client.get("/api/master/report/PLTR")
    assert res.status_code == 200
    data = res.json()
    assert data["ticker"] == "PLTR"
    assert data["company_name"] == "Palantir Technologies Inc."
    assert data["current_price"] == 42.50
    assert data["reconciliation_risk_score"] == "Medium"
    assert "Expanding government" in data["ground_truth_status"]
    
    assert "retail_overlay" in data
    assert data["retail_overlay"]["has_data"] is True
    assert data["retail_overlay"]["recommendation"] == "BUY"

    assert "smart_money_overlay" in data
    assert data["smart_money_overlay"]["has_data"] is True
    assert data["smart_money_overlay"]["conviction_tier"] == "Tier-1 Alpha"
    assert len(data["smart_money_overlay"]["inflow_ledger"]) == 1

    assert "synthesis" in data
    assert data["synthesis"]["has_data"] is True
    assert data["synthesis"]["archetype"] == "The Rocket"


@pytest.mark.asyncio
async def test_api_ticker_archetype_progression(app_client: AsyncClient):
    """Verify GET /api/analytics/ticker/{ticker}/archetypes returns chronological lifecycle states."""
    res = await app_client.get("/api/analytics/ticker/PLTR/archetypes")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    # Should contain yesterday (Silent Accumulation) and today (The Rocket)
    assert len(data) >= 2
    assert data[0]["archetype"] == "Silent Accumulation"
    assert data[-1]["archetype"] == "The Rocket"


@pytest.mark.asyncio
async def test_api_smart_money_only_ticker_analytics(app_client: AsyncClient):
    """Verify GET /api/analytics/ticker/{ticker} works for Smart-Money-only tickers like ACN."""
    res = await app_client.get("/api/analytics/ticker/ACN")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["ticker"] == "ACN"
    assert data[0]["current_price"] == 285.00
    assert data[0]["target_price"] == 330.00
    assert data[0]["recommendation"] == "BUY"
    assert data[0]["smart_money_verdict"] == "Tier-1 Alpha"


@pytest.mark.asyncio
async def test_api_detail_endpoints_with_date_filter(app_client: AsyncClient):
    """Verify that detail endpoints for Retail, Smart Money, and Master Report respect the ?date= query parameter."""
    # 1. Retail Detail Endpoint
    # Latest / without date -> returns 2026-11-01 BUY
    res_latest_retail = await app_client.get("/api/retail/report/PLTR")
    assert res_latest_retail.status_code == 200
    assert res_latest_retail.json()["recommendation"] == "BUY"

    # Specific historical date 2026-10-31 -> returns HOLD
    res_hist_retail = await app_client.get("/api/retail/report/PLTR?date=2026-10-31")
    assert res_hist_retail.status_code == 200
    assert res_hist_retail.json()["recommendation"] == "HOLD"
    assert res_hist_retail.json()["date"].startswith("2026-10-31")

    # Non-existent date -> 404
    res_404_retail = await app_client.get("/api/retail/report/PLTR?date=2025-01-01")
    assert res_404_retail.status_code == 404

    # 2. Smart Money Detail Endpoint
    # Latest -> Tier-1 Alpha
    res_latest_sm = await app_client.get("/api/smart-money/report/PLTR")
    assert res_latest_sm.status_code == 200
    assert res_latest_sm.json()["conviction_tier"] == "Tier-1 Alpha"

    # Historical date 2026-10-31 -> Moderate Cluster
    res_hist_sm = await app_client.get("/api/smart-money/report/PLTR?date=2026-10-31")
    assert res_hist_sm.status_code == 200
    assert res_hist_sm.json()["conviction_tier"] == "Moderate Cluster"
    assert res_hist_sm.json()["date"].startswith("2026-10-31")

    # 3. Master Report Endpoint
    # Latest -> archetype "The Rocket"
    res_latest_master = await app_client.get("/api/master/report/PLTR")
    assert res_latest_master.status_code == 200
    assert res_latest_master.json()["synthesis"]["archetype"] == "The Rocket"

    # Historical date 2026-10-31 -> archetype "Silent Accumulation"
    res_hist_master = await app_client.get("/api/master/report/PLTR?date=2026-10-31")
    assert res_hist_master.status_code == 200
    assert res_hist_master.json()["synthesis"]["archetype"] == "Silent Accumulation"
    assert res_hist_master.json()["recommendation"] == "HOLD"
    assert res_hist_master.json()["smart_money_overlay"]["conviction_tier"] == "Moderate Cluster"
