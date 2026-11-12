import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database import Base, get_db
from app.models import (
    RetailSentimentReport,
    CoreEquityReport,
    CoreEquityRaw,
    DailyTicker,
    SynthesisReport,
    OptionsWhaleReport,
    OptionsWhaleTicker,
    SmartMoneyReport,
)
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def test_db():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async with async_session() as session:
        # Seed normalized CoreEquityRaw -> CoreEquityReport + DailyTicker -> RetailSentimentReport
        raw1 = CoreEquityRaw(ticker="AAPL", raw_metrics={"industry": "Consumer Electronics", "sector": "Technology", "pe_ratio": 30.5})
        raw2 = CoreEquityRaw(ticker="AAPL", raw_metrics={"industry": "Consumer Electronics", "sector": "Technology", "pe_ratio": 31.0})
        raw3 = CoreEquityRaw(ticker="NVDA", raw_metrics={"industry": "Semiconductors", "sector": "Technology", "pe_ratio": 55.0})
        raw4 = CoreEquityRaw(ticker="GOOG", raw_metrics={"industry": "Internet", "sector": "Technology", "pe_ratio": 24.0})
        session.add_all([raw1, raw2, raw3, raw4])
        await session.flush()

        c1 = CoreEquityReport(
            ticker="AAPL", date=datetime(2026, 10, 28, 12, 0, 0, tzinfo=timezone.utc), core_raw_id=raw1.id,
            current_price=220.0, target_price=240.0, ground_truth_status="Solid hardware margins",
            ground_truth_filings_news="10-Q showed strong services growth", events_happenings="New product launch scheduled",
            risk_score="Low", risk_analysis="Consensus aligns with retail sentiment", actionable_insight="Track Q4 services revenue",
        )
        c2 = CoreEquityReport(
            ticker="AAPL", date=datetime(2026, 10, 29, 12, 0, 0, tzinfo=timezone.utc), core_raw_id=raw2.id,
            current_price=225.0, target_price=245.0, ground_truth_status="Services reached all time high",
            ground_truth_filings_news="8-K update on international market", events_happenings="Retail store expansion in Asia",
            risk_score="Low", risk_analysis="Momentum building sustainably", actionable_insight="Monitor gross margin stability",
        )
        c3 = CoreEquityReport(
            ticker="NVDA", date=datetime(2026, 10, 29, 12, 0, 0, tzinfo=timezone.utc), core_raw_id=raw3.id,
            current_price=130.0, target_price=150.0, ground_truth_status="Data center monopoly",
            ground_truth_filings_news="10-Q confirmed backlog", events_happenings="New architecture revealed",
            risk_score="Medium", risk_analysis="Priced for perfection", actionable_insight="Track Blackwell shipments",
        )
        c4 = CoreEquityReport(
            ticker="GOOG", date=datetime(2026, 10, 29, 12, 0, 0, tzinfo=timezone.utc), core_raw_id=raw4.id,
            current_price=280.0, target_price=350.0, ground_truth_status="Dominant search and cloud growth",
            ground_truth_filings_news="10-Q confirmed strong cloud margins", events_happenings="Gemini 3 launch",
            risk_score="Low", risk_analysis="Fundamentals strong", actionable_insight="Monitor advertising growth",
        )
        session.add_all([c1, c2, c3, c4])
        await session.flush()

        d1 = DailyTicker(ticker="AAPL", date=c1.date, rank=1, mention_count=100, engagement_score=500.0)
        d2 = DailyTicker(ticker="AAPL", date=c2.date, rank=1, mention_count=120, engagement_score=600.0)
        d3 = DailyTicker(ticker="NVDA", date=c3.date, rank=2, mention_count=90, engagement_score=400.0)
        d4 = DailyTicker(ticker="GOOG", date=c4.date, rank=3, mention_count=80, engagement_score=350.0)
        session.add_all([d1, d2, d3, d4])
        await session.flush()

        r1 = RetailSentimentReport(
            ticker="AAPL", date=c1.date, core_intel_id=c1.id, daily_ticker_id=d1.id,
            community_sentiment="60% Bullish", community_hype="iPhone 18 rumors",
            reconciliation_actionable_insight="Track Q4 services revenue", recommendation="BUY",
            recommendation_rationale="Services growth offset hardware maturity",
        )
        r2 = RetailSentimentReport(
            ticker="AAPL", date=c2.date, core_intel_id=c2.id, daily_ticker_id=d2.id,
            community_sentiment="75% Bullish", community_hype="Services revenue explosion",
            reconciliation_actionable_insight="Monitor gross margin stability", recommendation="BUY",
            recommendation_rationale="Services beat consensus",
        )
        r3 = RetailSentimentReport(
            ticker="NVDA", date=c3.date, core_intel_id=c3.id, daily_ticker_id=d3.id,
            community_sentiment="85% Bullish", community_hype="AI GPU demand soaring",
            reconciliation_actionable_insight="Track Blackwell shipments", recommendation="HOLD",
            recommendation_rationale="High valuation warrants holding",
        )
        r4 = RetailSentimentReport(
            ticker="GOOG", date=c4.date, core_intel_id=c4.id, daily_ticker_id=d4.id,
            community_sentiment="70% Bullish", community_hype="Cloud TPU and Gemini momentum",
            reconciliation_actionable_insight="Monitor advertising growth", recommendation="BUY",
            recommendation_rationale="Search moats intact",
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
        res = await client.get("/api/dates")
        assert res.status_code == 200
        dates = res.json()
        assert dates == ["2026-10-29", "2026-10-28"]

@pytest.mark.asyncio
async def test_get_retail_reports_by_date(test_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Specific date
        res = await client.get("/api/retail/reports?date=2026-10-29")
        assert res.status_code == 200
        reports = res.json()
        assert len(reports) == 3
        tickers = [r["ticker"] for r in reports]
        assert "AAPL" in tickers
        assert "NVDA" in tickers
        assert "GOOG" in tickers
        
        # Default latest date
        res_latest = await client.get("/api/retail/reports")
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

        # Report alias resolution: requesting /api/master/report/GOOGL should return GOOG report
        res_rep_alias = await client.get("/api/master/report/GOOGL")
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

    # Roman numerals, slang and noise words should be excluded
    noise_extracted = extract_tickers_from_text("Phase III trials for WW III or Part II NFA DYOR")
    assert "III" not in noise_extracted
    assert "II" not in noise_extracted
    assert "NFA" not in noise_extracted
    assert "DYOR" not in noise_extracted

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

        # NVDA only has 1 report in default test_db -> cannot generate
        res_nvda_post = await client.post("/api/analytics/ticker/NVDA/meta-analysis")
        assert res_nvda_post.status_code == 400
        assert "At least 2 historical reports" in res_nvda_post.json()["detail"]


@pytest.mark.asyncio
async def test_cross_engine_ticker_history_progression(test_db):
    """
    Verify that when a ticker has multiple runs across different engines
    (e.g. Day 1: Options Whale + Synthesis, Day 2: Retail + Synthesis, Day 3: Options Whale + Synthesis),
    all 3 runs are unified in get_ticker_history and the ticker can generate meta-analysis.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Seed multi-engine runs for MSFT
        engine = create_async_engine(TEST_DATABASE_URL, echo=False)
        async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
        
        # We need to insert into the test_db's actual session/engine
        # The override in test_db fixture uses the session from test_db.
        # But we can query the app client directly if we use app.dependency_overrides.
        pass

    # Better approach: test with isolated session
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # Day 1: Options Whale only (no Retail)
        raw_m1 = CoreEquityRaw(ticker="MSFT", raw_metrics={"pe_ratio": 32.0})
        session.add(raw_m1)
        await session.flush()
        c1 = CoreEquityReport(
            ticker="MSFT",
            date=datetime(2026, 11, 4, 12, 0, 0, tzinfo=timezone.utc),
            core_raw_id=raw_m1.id,
            current_price=410.0,
            target_price=500.0,
            ground_truth_status="Cloud Azure growth",
            risk_score="Low",
            actionable_insight="Track Copilot ARR",
        )
        session.add(c1)
        await session.flush()

        owt1 = OptionsWhaleTicker(ticker="MSFT", date=c1.date, rank=1, whale_score=85.0)
        session.add(owt1)
        await session.flush()
        opt1 = OptionsWhaleReport(
            ticker="MSFT",
            date=datetime(2026, 11, 4, 12, 5, 0, tzinfo=timezone.utc),
            core_intel_id=c1.id,
            options_whale_ticker_id=owt1.id,
        )
        syn1 = SynthesisReport(
            ticker="MSFT",
            date=datetime(2026, 11, 4, 12, 10, 0, tzinfo=timezone.utc),
            core_intel_id=c1.id,
            options_whale_report_id=None,
            archetype="Silent Accumulation",
            timing_edge_score=90.0,
            recommended_action="EARLY SWING BUY",
            retail_awareness_level="Zero Awareness (Stealth)"
        )
        session.add_all([opt1, syn1])

        # Day 2: Retail Momentum
        raw_m2 = CoreEquityRaw(ticker="MSFT", raw_metrics={"pe_ratio": 33.0})
        session.add(raw_m2)
        await session.flush()
        c2 = CoreEquityReport(
            ticker="MSFT",
            date=datetime(2026, 11, 6, 12, 0, 0, tzinfo=timezone.utc),
            core_raw_id=raw_m2.id,
            current_price=420.0,
            target_price=500.0,
            ground_truth_status="Copilot adoption expanding",
            risk_score="Low",
            actionable_insight="Monitor enterprise renewals",
        )
        session.add(c2)
        await session.flush()

        ret2 = RetailSentimentReport(
            ticker="MSFT",
            date=datetime(2026, 11, 6, 12, 5, 0, tzinfo=timezone.utc),
            core_intel_id=c2.id,
            community_sentiment="Bullish",
            community_hype="Copilot viral demos",
            recommendation="BUY",
            recommendation_rationale="Azure accelerating"
        )
        syn2 = SynthesisReport(
            ticker="MSFT",
            date=datetime(2026, 11, 6, 12, 10, 0, tzinfo=timezone.utc),
            core_intel_id=c2.id,
            archetype="The Rocket",
            timing_edge_score=80.0,
            recommended_action="STRONG BUY",
            retail_awareness_level="Mainstream Momentum"
        )
        session.add_all([ret2, syn2])

        # Day 3: Options Whale only (no Retail)
        raw_m3 = CoreEquityRaw(ticker="MSFT", raw_metrics={"pe_ratio": 34.0})
        session.add(raw_m3)
        await session.flush()
        c3 = CoreEquityReport(
            ticker="MSFT",
            date=datetime(2026, 11, 7, 12, 0, 0, tzinfo=timezone.utc),
            core_raw_id=raw_m3.id,
            current_price=430.0,
            target_price=500.0,
            ground_truth_status="Datacenter capacity scale",
            risk_score="Low",
            actionable_insight="Track GPU lease commitments",
        )
        session.add(c3)
        await session.flush()

        owt3 = OptionsWhaleTicker(ticker="MSFT", date=c3.date, rank=1, whale_score=92.0)
        session.add(owt3)
        await session.flush()
        opt3 = OptionsWhaleReport(
            ticker="MSFT",
            date=datetime(2026, 11, 7, 12, 5, 0, tzinfo=timezone.utc),
            core_intel_id=c3.id,
            options_whale_ticker_id=owt3.id,
        )
        syn3 = SynthesisReport(
            ticker="MSFT",
            date=datetime(2026, 11, 7, 12, 10, 0, tzinfo=timezone.utc),
            core_intel_id=c3.id,
            archetype="Silent Accumulation",
            timing_edge_score=95.0,
            recommended_action="EARLY SWING BUY",
            retail_awareness_level="Zero Awareness (Stealth)"
        )
        session.add_all([opt3, syn3])
        await session.commit()

        from app.crud import get_ticker_history
        history = await get_ticker_history(session, "MSFT")
        assert len(history) == 3
        assert history[0].current_price == 410.0
        assert history[0].recommendation == "BUY"
        assert history[1].current_price == 420.0
        assert history[1].recommendation == "BUY"
        assert history[2].current_price == 430.0
        assert history[2].recommendation == "BUY"

