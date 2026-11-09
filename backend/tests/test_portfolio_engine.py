import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.database import Base
from app.models import (
    PortfolioAccount,
    PortfolioPosition,
    PortfolioSnapshot,
    SynthesisReport,
    CoreEquityReport,
)
from app.crud import (
    get_or_create_portfolio_account,
    get_open_positions,
    get_closed_positions,
    get_portfolio_snapshots,
)
from app.portfolio_engine import (
    qualify_synthesis_signals,
    execute_market_open_orders,
    evaluate_market_close_exits,
    close_position_manually,
    record_daily_portfolio_snapshot,
    get_portfolio_summary_metrics,
    get_archetype_holding_horizon,
    ROCKET_HOLDING_DAYS_PRIOR,
    SILENT_ACCUMULATION_HOLDING_DAYS_PRIOR,
)

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


@pytest.mark.asyncio
async def test_qualify_synthesis_signals(test_db: AsyncSession):
    """Verify qualification filters by archetype (The Rocket, Silent Accumulation) and score >= 75.0."""
    now = datetime(2026, 11, 8, 19, 0, tzinfo=timezone.utc)
    d_str = "2026-11-08"

    # Add core equity report for linking
    core = CoreEquityReport(ticker="NVDA", company_name="Nvidia", current_price=100.0)
    test_db.add(core)
    await test_db.commit()
    await test_db.refresh(core)

    # 1. High conviction Rocket (Score 85) -> QUALIFIES
    r1 = SynthesisReport(
        ticker="NVDA",
        date=now,
        archetype="The Rocket",
        timing_edge_score=85.0,
        core_intel_id=core.id,
        retail_awareness_level="Emerging",
        synthesis_diagnosis="Strong breakout",
        recommended_action="STRONG BUY",
    )
    # 2. High conviction Silent Accumulation (Score 78) -> QUALIFIES
    r2 = SynthesisReport(
        ticker="AAPL",
        date=now,
        archetype="Silent Accumulation",
        timing_edge_score=78.0,
        core_intel_id=core.id,
        retail_awareness_level="Zero Awareness (Stealth)",
        synthesis_diagnosis="Institutional inflow",
        recommended_action="EARLY SWING BUY",
    )
    # 3. Retail Trap (Score 88) -> REJECTED (wrong archetype)
    r3 = SynthesisReport(
        ticker="GME",
        date=now,
        archetype="The Retail Trap",
        timing_edge_score=88.0,
        core_intel_id=core.id,
        retail_awareness_level="Saturated Hype",
        synthesis_diagnosis="Trap",
        recommended_action="AVOID/SHORT",
    )
    # 4. Low conviction Rocket (Score 65) -> REJECTED (score < 75.0)
    r4 = SynthesisReport(
        ticker="AMD",
        date=now,
        archetype="The Rocket",
        timing_edge_score=65.0,
        core_intel_id=core.id,
        retail_awareness_level="Emerging",
        synthesis_diagnosis="Weak rocket",
        recommended_action="PASS",
    )
    test_db.add_all([r1, r2, r3, r4])
    await test_db.commit()

    candidates = await qualify_synthesis_signals(test_db, date_str=d_str)
    assert len(candidates) == 2
    tickers = [c["ticker"] for c in candidates]
    assert "NVDA" in tickers
    assert "AAPL" in tickers
    assert "GME" not in tickers
    assert "AMD" not in tickers


@pytest.mark.asyncio
async def test_market_open_order_execution_and_queue_discipline(test_db: AsyncSession):
    """Verify fixed $10k allocation, stop/target prices, and max 10 position capacity constraint."""
    now = datetime(2026, 11, 8, 19, 0, tzinfo=timezone.utc)
    d_str = "2026-11-08"

    for i in range(12):
        sym = f"TICK{i}"
        r = SynthesisReport(
            ticker=sym,
            date=now,
            archetype="The Rocket",
            timing_edge_score=90.0 - i,
            retail_awareness_level="Emerging",
            synthesis_diagnosis="Test candidate",
            recommended_action="STRONG BUY",
        )
        test_db.add(r)
    await test_db.commit()

    # Provide mock prices: each ticker is $100.0 (100 shares = $10,000)
    mock_prices = {f"TICK{i}": 100.0 for i in range(12)}
    res = await execute_market_open_orders(
        test_db, date_str=d_str, mock_prices=mock_prices, mock_spy_price=580.0
    )

    assert res["status"] == "success"
    assert res["executed_count"] == 10  # strictly capped at 10 positions!
    assert len(res["skipped"]) == 2     # remaining 2 skipped due to capacity_full
    assert res["skipped"][0]["reason"] == "capacity_full"

    # Verify open positions
    open_pos = await get_open_positions(test_db)
    assert len(open_pos) == 10
    sample_pos = open_pos[0]
    assert sample_pos.shares == 100
    assert sample_pos.entry_price == 100.0
    assert sample_pos.stop_loss_price == 95.0   # -5.0% Rocket stop
    assert sample_pos.target_price == 112.0     # +12.0% Rocket take profit
    assert sample_pos.spy_entry_price == 580.0

    account = await get_or_create_portfolio_account(test_db)
    assert account.cash_balance == 0.0  # 10 x $10,000 = $100,000 spent


@pytest.mark.asyncio
async def test_market_close_exit_rules(test_db: AsyncSession):
    """Verify stop-loss, take-profit, time-decay exit triggers and mark-to-market updates."""
    account = await get_or_create_portfolio_account(test_db)
    entry_dt = datetime(2026, 11, 1, 9, 30, tzinfo=timezone.utc)

    # Position 1: Hits Hard Stop-Loss (-5.0% for Rocket)
    p1 = PortfolioPosition(
        account_id=account.id,
        ticker="STOPP",
        archetype="The Rocket",
        conviction_score=85.0,
        status="OPEN",
        shares=100,
        entry_date=entry_dt,
        entry_price=100.0,
        current_price=100.0,
        stop_loss_price=95.0,
        target_price=112.0,
        holding_days=2,
    )
    # Position 2: Hits Take-Profit (+12.0% for Rocket)
    p2 = PortfolioPosition(
        account_id=account.id,
        ticker="PROFIT",
        archetype="The Rocket",
        conviction_score=88.0,
        status="OPEN",
        shares=100,
        entry_date=entry_dt,
        entry_price=100.0,
        current_price=100.0,
        stop_loss_price=95.0,
        target_price=112.0,
        holding_days=3,
    )
    # Position 3: Hits Time Exit (Rocket holds 9 days > 8 day horizon)
    p3 = PortfolioPosition(
        account_id=account.id,
        ticker="TIMED",
        archetype="The Rocket",
        conviction_score=80.0,
        status="OPEN",
        shares=100,
        entry_date=entry_dt - timedelta(days=9),
        entry_price=100.0,
        current_price=100.0,
        stop_loss_price=95.0,
        target_price=112.0,
        holding_days=8,
    )
    # Position 4: Normal holding (flat at $102, holding 3 days < 22 days)
    p4 = PortfolioPosition(
        account_id=account.id,
        ticker="HOLDING",
        archetype="Silent Accumulation",
        conviction_score=82.0,
        status="OPEN",
        shares=100,
        entry_date=entry_dt,
        entry_price=100.0,
        current_price=100.0,
        stop_loss_price=92.0,
        target_price=120.0,
        holding_days=2,
    )
    test_db.add_all([p1, p2, p3, p4])
    account.cash_balance = 60000.0  # 4 x $10,000 allocated
    await test_db.commit()

    eval_dt = datetime(2026, 11, 4, 16, 0, tzinfo=timezone.utc)
    mock_prices = {
        "STOPP": 92.0,     # -8.0% <= -7% -> STOP_LOSS
        "PROFIT": 116.0,   # +16.0% >= +15% -> TAKE_PROFIT
        "TIMED": 101.0,    # +1.0%, but 9 days >= 8 days -> TIME_EXIT
        "HOLDING": 102.0,  # +2.0%, 3 days < 22 days -> STAYS OPEN
    }

    res = await evaluate_market_close_exits(
        test_db,
        mock_prices=mock_prices,
        mock_spy_price=590.0,
        exit_date=eval_dt,
    )

    assert res["status"] == "success"
    assert res["closed_count"] == 3
    assert res["updated_count"] == 1

    closed_reasons = {c["ticker"]: c["exit_reason"] for c in res["closed_positions"]}
    assert closed_reasons["STOPP"] == "STOP_LOSS"
    assert closed_reasons["PROFIT"] == "TAKE_PROFIT"
    assert closed_reasons["TIMED"] == "TIME_EXIT"

    # Verify HOLDING is still open
    open_now = await get_open_positions(test_db, account.id)
    assert len(open_now) == 1
    assert open_now[0].ticker == "HOLDING"
    assert open_now[0].current_price == 102.0
    assert open_now[0].unrealized_pnl == 200.0


@pytest.mark.asyncio
async def test_manual_position_liquidation(test_db: AsyncSession):
    """Verify manual position liquidation override."""
    account = await get_or_create_portfolio_account(test_db)
    p = PortfolioPosition(
        account_id=account.id,
        ticker="TSLA",
        archetype="The Rocket",
        conviction_score=85.0,
        status="OPEN",
        shares=50,
        entry_date=datetime(2026, 11, 1, 9, 30, tzinfo=timezone.utc),
        entry_price=200.0,
        stop_loss_price=186.0,
        target_price=230.0,
        spy_entry_price=580.0,
    )
    test_db.add(p)
    account.cash_balance = 90000.0
    await test_db.commit()
    await test_db.refresh(p)

    # Manually close at $210.0
    closed = await close_position_manually(
        test_db, position_id=p.id, mock_price=210.0, mock_spy_price=585.0
    )
    assert closed.status == "CLOSED"
    assert closed.exit_reason == "MANUAL"
    assert closed.exit_price == 210.0
    assert closed.realized_pnl == 500.0  # (210 - 200) * 50
    assert closed.return_pct == 5.0

    # Repeating manual close on already closed position must raise ValueError
    with pytest.raises(ValueError, match="already CLOSED"):
        await close_position_manually(test_db, position_id=p.id, mock_price=210.0)


@pytest.mark.asyncio
async def test_portfolio_summary_metrics(test_db: AsyncSession):
    """Verify calculated KPI summary cards on portfolio dashboard."""
    account = await get_or_create_portfolio_account(test_db)
    metrics = await get_portfolio_summary_metrics(test_db)
    assert metrics["initial_balance"] == 100000.0
    assert metrics["cash_balance"] == 100000.0
    assert metrics["total_equity"] == 100000.0
    assert metrics["open_positions_count"] == 0
    assert metrics["closed_trades_count"] == 0
    assert metrics["win_rate_pct"] == 0.0
