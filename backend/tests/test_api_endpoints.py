import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database import Base, get_db
from app.models import (
    CoreEquityRaw,
    CoreEquityReport,
    DailyTicker,
    RetailSentimentReport,
    SmartMoneyReport,
    SmartMoneyTicker,
    SynthesisReport,
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
        raw_tsla = CoreEquityRaw(ticker="TSLA", raw_metrics={"industry": "Auto", "sector": "Consumer"})
        session.add(raw_tsla)
        await session.flush()
        core_tsla = CoreEquityReport(
            ticker="TSLA",
            date=now,
            core_raw_id=raw_tsla.id,
            current_price=220.0,
            target_price=250.0,
            ground_truth_status="Verified",
            risk_score="Medium",
            risk_analysis="Analysis",
            actionable_insight="Insight",
        )
        dt_tsla = DailyTicker(ticker="TSLA", date=now, rank=1, mention_count=150, engagement_score=100.0)
        session.add_all([core_tsla, dt_tsla])
        await session.flush()

        retail = RetailSentimentReport(
            ticker="TSLA",
            date=now,
            core_intel_id=core_tsla.id,
            daily_ticker_id=dt_tsla.id,
            recommendation="BUY",
            recommendation_rationale="High volume breakout.",
            community_sentiment="Bullish",
            community_hype="Extreme",
            reconciliation_actionable_insight="Insight",
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
        raw_nvda = CoreEquityRaw(
            ticker="NVDA",
            raw_metrics={"trailingPE": 45.2, "forwardPE": 28.5},
            raw_news=[],
        )
        session.add(raw_nvda)
        await session.flush()
        intel = CoreEquityReport(
            ticker="NVDA",
            date=now,
            core_raw_id=raw_nvda.id,
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
        )
        dt_nvda = DailyTicker(ticker="NVDA", date=now, rank=1, mention_count=300, engagement_score=100.0)
        smt_nvda = SmartMoneyTicker(ticker="NVDA", date=now, rank=2, conviction_score=9.2, top_buyer_summary="Heavy Inflow")
        session.add_all([intel, dt_nvda, smt_nvda])
        await session.flush()

        ret_nvda = RetailSentimentReport(
            ticker="NVDA", date=now, core_intel_id=intel.id, daily_ticker_id=dt_nvda.id,
            community_sentiment="Bullish", community_hype="Blackwell ramp",
            recommendation="BUY", recommendation_rationale="Strong datacenter demand.",
        )
        sm_nvda = SmartMoneyReport(
            ticker="NVDA", date=now, core_intel_id=intel.id, smart_money_ticker_id=smt_nvda.id,
            conviction_tier="Tier-1 Alpha", actionable_thesis="Heavy Inflow",
        )
        session.add_all([ret_nvda, sm_nvda])
        await session.flush()

        synthesis = SynthesisReport(
            ticker="NVDA",
            date=now,
            core_intel_id=intel.id,
            retail_report_id=ret_nvda.id,
            smart_money_report_id=sm_nvda.id,
            archetype="The Rocket",
            smart_money_flow="Heavy Inflow",
            retail_awareness_level="Mainstream Hype",
            timing_edge_score=85.0,
            synthesis_diagnosis="Dual alignment confirmed.",
            recommended_action="ACCUMULATE",
        )
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
        raw_acn = CoreEquityRaw(
            ticker="ACN",
            raw_metrics={"marketCap": 210000000000, "trailingPE": 28.4, "forwardPE": 23.1, "beta": 1.08},
            raw_news=[],
        )
        session.add(raw_acn)
        await session.flush()

        intel = CoreEquityReport(
            ticker="ACN",
            date=now,
            core_raw_id=raw_acn.id,
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
        )
        smt_acn = SmartMoneyTicker(
            ticker="ACN",
            date=now,
            rank=1,
            conviction_score=8.7,
            cluster_count=4,
            total_buy_volume=1250000.0,
            top_buyer_summary="CEO & COO Form 4 Accumulation",
        )
        session.add_all([intel, smt_acn])
        await session.flush()

        sm_rep = SmartMoneyReport(
            ticker="ACN",
            date=now,
            core_intel_id=intel.id,
            smart_money_ticker_id=smt_acn.id,
            conviction_tier="High Conviction Cluster",
            inflow_ledger=[
                {"type": "Form 4", "name": "Julie Sweet", "role": "CEO", "price": "$348.00", "amount": "$750,000", "date": "2026-10-25", "delta_own": "+15%"}
            ],
            political_catalyst_analysis="DoD and federal IT modernization contracts pending.",
            corporate_catalyst_analysis="Enterprise GenAI bookings acceleration.",
            catalyst_horizon="3 - 6 Months",
            actionable_thesis="Front-run federal cloud award season.",
        )
        session.add(sm_rep)
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


@pytest.mark.asyncio
async def test_scheduler_status_endpoint(app_client):
    client, _ = app_client
    res = await client.get("/api/scheduler/status")
    assert res.status_code == 200
    data = res.json()
    assert "scheduler_running" in data
    assert data["timezone"] == "Asia/Singapore"
    assert "jobs" in data
    assert any(j["id"] == "daily_market_intelligence_pipeline" for j in data["jobs"])
    job = next(j for j in data["jobs"] if j["id"] == "daily_market_intelligence_pipeline")
    assert job["misfire_grace_time"] == 3600
    assert job["coalesce"] is True


