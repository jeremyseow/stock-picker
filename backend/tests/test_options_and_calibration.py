import pytest
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone

from app.main import app
from app.database import get_db, Base
from app.options_scorer import score_options_flow, rank_whale_candidates
from app.scoring_weights import get_active_weights, update_active_weights, reset_weights_to_default
from app.models import CoreEquityReport, OptionsWhaleTicker, OptionsWhaleReport, SynthesisReport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_db():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def client(test_db):
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


def test_options_scoring_and_ranking():
    """Verify options flow scoring weights volume-to-OI spikes, call premium, and P/C ratio."""
    bullish_opt = {
        "ticker": "NVDA",
        "current_price": 140.0,
        "peak_oi_ratio": 4.5,
        "net_bullish_premium": 500000.0,
        "put_call_ratio": 0.25,
        "unusual_contracts": [
            {
                "type": "CALL",
                "strike": 160.0,
                "expiration": "2026-11-20",
                "ratio": 4.5,
                "premium": 500000.0,
                "is_sweep": True,
            }
        ],
    }

    scored = score_options_flow(bullish_opt)
    assert scored["ticker"] == "NVDA"
    assert scored["whale_score"] >= 65.0
    assert scored["sentiment_bias"] == "Extremely Bullish Sweeps"
    assert "160.0C" in scored["top_strike_summary"]

    ranked = rank_whale_candidates([bullish_opt])
    assert len(ranked) == 1
    assert ranked[0]["rank"] == 1


def test_scoring_weights_registry_persistence():
    """Verify active weights can be updated, read, and reset cleanly."""
    reset_weights_to_default()
    initial_w = get_active_weights()
    assert "smart_money" in initial_w
    assert "options_whale" in initial_w

    updated = update_active_weights({
        "smart_money": {"c_suite_weight": 3.8},
        "options_whale": {"min_volume_oi_ratio": 3.0},
    })
    assert updated["smart_money"]["c_suite_weight"] == 3.8
    assert updated["options_whale"]["min_volume_oi_ratio"] == 3.0

    reset_weights_to_default()
    restored = get_active_weights()
    assert restored["smart_money"]["c_suite_weight"] == 3.0


@pytest.mark.anyio
async def test_options_api_endpoints(client: AsyncClient, test_db: AsyncSession):
    """Verify canonical options endpoints return structured options flow data."""
    now = datetime.now(timezone.utc)
    core = CoreEquityReport(
        ticker="PLTR",
        company_name="Palantir Technologies",
        sector="Technology",
        industry="Software",
        current_price=45.0,
        target_price=60.0,
        ground_truth_status="Strong government defense contracts.",
        date=now,
    )
    test_db.add(core)
    await test_db.commit()
    await test_db.refresh(core)

    ow_ticker = OptionsWhaleTicker(
        ticker="PLTR",
        rank=1,
        whale_score=85.0,
        unusual_oi_multiplier=3.8,
        net_bullish_premium=400000.0,
        put_call_ratio=0.22,
        top_strike_summary="$50C 11/20 (3.8x OI, $400k)",
        date=now,
    )
    ow_rep = OptionsWhaleReport(
        ticker="PLTR",
        core_intel_id=core.id,
        company_name="Palantir Technologies",
        sector="Technology",
        industry="Software",
        current_price=45.0,
        target_price=60.0,
        rank=1,
        whale_score=85.0,
        unusual_oi_multiplier=3.8,
        put_call_ratio=0.22,
        net_bullish_premium=400000.0,
        sentiment_bias="Extremely Bullish Sweeps",
        top_strike_summary="$50C 11/20 (3.8x OI, $400k)",
        unusual_contracts=[{"strike": 50.0, "type": "CALL", "ratio": 3.8}],
        date=now,
    )
    test_db.add(ow_ticker)
    test_db.add(ow_rep)
    await test_db.commit()

    # 1. /api/options/today
    r_today = await client.get("/api/options/today")
    assert r_today.status_code == 200
    today_data = r_today.json()
    assert len(today_data) == 1
    assert today_data[0]["ticker"] == "PLTR"
    assert today_data[0]["whale_score"] == 85.0

    # 2. /api/options/report/PLTR
    r_detail = await client.get("/api/options/report/PLTR")
    assert r_detail.status_code == 200
    detail_data = r_detail.json()
    assert detail_data["ticker"] == "PLTR"
    assert detail_data["whale_score"] == 85.0
    assert detail_data["company_name"] == "Palantir Technologies"
    assert len(detail_data["unusual_contracts"]) == 1

    # 3. /api/options/reports?date=
    date_str = now.strftime("%Y-%m-%d")
    r_hist = await client.get(f"/api/options/reports?date={date_str}")
    assert r_hist.status_code == 200
    hist_data = r_hist.json()
    assert len(hist_data) == 1
    assert hist_data[0]["ticker"] == "PLTR"


@pytest.mark.anyio
async def test_calibration_scorecard_and_apply_weights(client: AsyncClient, test_db: AsyncSession):
    """Verify calibration scorecard computation and weight application endpoints."""
    # 1. /api/calibration/scorecard
    r_scorecard = await client.get("/api/calibration/scorecard")
    assert r_scorecard.status_code == 200
    sc_data = r_scorecard.json()
    assert "overall_hit_rate_t30" in sc_data
    assert "archetype_scorecard" in sc_data
    assert "The Rocket" in sc_data["archetype_scorecard"]
    assert "Silent Accumulation" in sc_data["archetype_scorecard"]
    assert "weight_comparison_items" in sc_data
    assert len(sc_data["weight_comparison_items"]) > 0

    # 2. /api/calibration/apply-weights
    r_apply = await client.post("/api/calibration/apply-weights")
    assert r_apply.status_code == 200
    apply_data = r_apply.json()
    assert apply_data["status"] == "success"
    assert "active_weights" in apply_data

    # Clean up weights
    reset_weights_to_default()


@pytest.mark.anyio
async def test_model_calibration_trigger_and_deduplication(client: AsyncClient, test_db: AsyncSession):
    """
    Verifies that:
    1. GET /api/calibration/scorecard reads cached data without creating duplicate DB records.
    2. POST /api/calibration/run manually triggers calibration.
    3. Multiple triggers when no changes occurred do NOT duplicate records in the database.
    """
    from sqlalchemy import select, func
    from app.models import ModelCalibrationRun

    # Initial state: 0 runs
    count_init = (await test_db.execute(select(func.count(ModelCalibrationRun.id)))).scalar_one()

    # 1. Trigger calibration explicitly via POST /api/calibration/run
    r_run1 = await client.post("/api/calibration/run")
    assert r_run1.status_code == 200
    data1 = r_run1.json()
    assert data1["has_changes"] is True
    run1_id = data1["id"]

    # Exactly 1 run should now exist
    count_after_run1 = (await test_db.execute(select(func.count(ModelCalibrationRun.id)))).scalar_one()
    assert count_after_run1 == count_init + 1

    # 2. Trigger calibration a second time with NO data or weight changes
    r_run2 = await client.post("/api/calibration/run")
    assert r_run2.status_code == 200
    data2 = r_run2.json()
    assert data2["has_changes"] is False
    assert data2["id"] == run1_id

    # Count must remain strictly unchanged (no duplicate created!)
    count_after_run2 = (await test_db.execute(select(func.count(ModelCalibrationRun.id)))).scalar_one()
    assert count_after_run2 == count_after_run1

    # 3. GET /api/calibration/scorecard retrieves scorecard without creating duplicate rows
    r_get = await client.get("/api/calibration/scorecard")
    assert r_get.status_code == 200
    data_get = r_get.json()
    assert data_get["id"] == run1_id

    count_after_get = (await test_db.execute(select(func.count(ModelCalibrationRun.id)))).scalar_one()
    assert count_after_get == count_after_run1


