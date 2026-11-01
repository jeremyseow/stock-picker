import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database import Base, get_db
from app.models import (
    CoreEquityIntel,
    DailyTicker,
    RetailReport,
    SmartMoneyReport,
    SmartMoneyTicker,
    SynthesisRecord,
)
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

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

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, async_session

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_canonical_retail_endpoints_and_removed_legacy(app_client):
    client, session_maker = app_client
    now = datetime.now(timezone.utc)

    async with session_maker() as session:
        retail = RetailReport(
            ticker="TSLA",
            date=now,
            rank=1,
            mention_count=150,
            current_price=220.0,
            target_price=250.0,
            recommendation="BUY",
            recommendation_rationale="High volume breakout.",
            community_sentiment="Bullish",
            community_hype="Extreme",
            ground_truth_status="Verified",
            reconciliation_risk_score="Medium",
            reconciliation_analysis="Analysis",
            reconciliation_actionable_insight="Insight",
            raw_metrics={"industry": "Auto", "sector": "Consumer"},
            raw_insider_data={"has_data": False},
        )
        session.add(retail)
        await session.commit()

    # Test canonical /api/retail/reports
    res_retail = await client.get("/api/retail/reports")
    assert res_retail.status_code == 200
    assert len(res_retail.json()) == 1
    assert res_retail.json()[0]["ticker"] == "TSLA"

    # Verify legacy /api/reports is removed (404)
    res_legacy = await client.get("/api/reports")
    assert res_legacy.status_code == 404

    # Test /api/retail/report/TSLA
    res_detail = await client.get("/api/retail/report/TSLA")
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert detail["ticker"] == "TSLA"
    assert detail["recommendation"] == "BUY"
    assert "core_intel" in detail


@pytest.mark.asyncio
async def test_canonical_master_report_and_removed_legacy(app_client):
    client, session_maker = app_client
    now = datetime.now(timezone.utc)

    async with session_maker() as session:
        intel = CoreEquityIntel(
            ticker="NVDA",
            date=now,
            company_name="NVIDIA Corporation",
            sector="Technology",
            industry="Semiconductors",
            current_price=135.0,
            target_price=175.0,
            ground_truth_status="Monopolistic Moat",
            ground_truth_filings_news="Record datacenter revenue.",
            events_happenings="Blackwell ramp in progress.",
            risk_score="Low",
            risk_analysis="Minimal debt, high margins.",
            actionable_insight="Key AI hardware standard.",
            raw_metrics={"trailingPE": 45.2, "forwardPE": 28.5},
            raw_news=[],
        )
        synthesis = SynthesisRecord(
            ticker="NVDA",
            date=now,
            archetype="The Rocket",
            retail_rank=1,
            retail_mentions=300,
            retail_sentiment="Bullish",
            smart_money_rank=2,
            smart_money_conviction=9.2,
            smart_money_flow="Heavy Inflow",
            retail_awareness_level="Mainstream Hype",
            timing_edge_score=85.0,
            synthesis_diagnosis="Dual alignment confirmed.",
            recommended_action="ACCUMULATE",
        )
        session.add(intel)
        session.add(synthesis)
        await session.commit()

    # Check canonical /api/master/report/{ticker}
    res_master = await client.get("/api/master/report/NVDA")
    assert res_master.status_code == 200

    data = res_master.json()
    assert data["ticker"] == "NVDA"
    assert data["company_name"] == "NVIDIA Corporation"
    assert data["synthesis"]["archetype"] == "The Rocket"

    # Verify legacy /api/reports/{ticker} is removed (404)
    res_legacy = await client.get("/api/reports/NVDA")
    assert res_legacy.status_code == 404


@pytest.mark.asyncio
async def test_smart_money_detail_embeds_core_intel(app_client):
    client, session_maker = app_client
    now = datetime.now(timezone.utc)

    async with session_maker() as session:
        sm_rep = SmartMoneyReport(
            ticker="ACN",
            date=now,
            rank=1,
            company_name="Accenture plc",
            sector="Technology",
            industry="IT Services",
            current_price=350.0,
            target_price=410.0,
            conviction_score=8.7,
            conviction_tier="High Conviction Cluster",
            cluster_count=4,
            total_buy_volume=1250000.0,
            top_buyer_summary="CEO & COO Form 4 Accumulation",
            inflow_ledger=[
                {"type": "Form 4", "name": "Julie Sweet", "role": "CEO", "price": "$348.00", "amount": "$750,000", "date": "2026-10-25", "delta_own": "+15%"}
            ],
            political_catalyst_analysis="DoD and federal IT modernization contracts pending.",
            corporate_catalyst_analysis="Enterprise GenAI bookings acceleration.",
            catalyst_horizon="3 - 6 Months",
            actionable_thesis="Front-run federal cloud award season.",
            ground_truth_status="Dominant Enterprise Moat",
            risk_score="Low",
            raw_metrics={"marketCap": 210000000000, "trailingPE": 28.4},
        )
        intel = CoreEquityIntel(
            ticker="ACN",
            date=now,
            company_name="Accenture plc",
            sector="Technology",
            industry="IT Services",
            current_price=350.0,
            target_price=410.0,
            ground_truth_status="Dominant Enterprise Moat",
            ground_truth_filings_news="10-K confirmed record consulting backlog.",
            events_happenings="Q4 earnings beat and dividend hike.",
            risk_score="Low",
            risk_analysis="Strong balance sheet, pristine debt/equity ratio.",
            actionable_insight="Institutional accumulation ahead of fiscal guidance.",
            raw_metrics={"marketCap": 210000000000, "trailingPE": 28.4, "forwardPE": 23.1, "beta": 1.08},
            raw_news=[],
        )
        session.add(sm_rep)
        session.add(intel)
        await session.commit()

    res = await client.get("/api/smart-money/report/ACN")
    assert res.status_code == 200
    data = res.json()
    assert data["ticker"] == "ACN"
    assert data["conviction_tier"] == "High Conviction Cluster"
    assert "core_intel" in data
    assert data["core_intel"]["has_data"] is True
    assert data["core_intel"]["ground_truth_filings_news"] == "10-K confirmed record consulting backlog."
    assert data["core_intel"]["risk_analysis"] == "Strong balance sheet, pristine debt/equity ratio."
    assert data["core_intel"]["raw_metrics"]["forwardPE"] == 23.1

