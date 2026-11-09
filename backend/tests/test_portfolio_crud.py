import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.database import Base
from app.models import PortfolioAccount, PortfolioPosition, PortfolioSnapshot
from app.crud import (
    get_or_create_portfolio_account,
    get_portfolio_account,
    update_portfolio_account,
    create_portfolio_position,
    get_open_positions,
    get_closed_positions,
    get_position_by_id,
    update_open_position_price,
    close_portfolio_position,
    save_portfolio_snapshot,
    get_portfolio_snapshots,
    get_latest_portfolio_snapshot,
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
async def test_portfolio_account_crud(test_db: AsyncSession):
    """Verify portfolio account creation, idempotency, and balance updating."""
    # 1. Initialize default account
    account = await get_or_create_portfolio_account(test_db)
    assert account.id is not None
    assert account.name == "Primary Fund"
    assert account.initial_balance == 100000.0
    assert account.cash_balance == 100000.0
    assert account.total_equity == 100000.0

    # 2. Re-fetching should return the existing account without duplicate
    account_again = await get_or_create_portfolio_account(test_db)
    assert account_again.id == account.id

    # 3. Fetch by ID
    fetched = await get_portfolio_account(test_db, account.id)
    assert fetched is not None
    assert fetched.id == account.id

    # 4. Update balances
    updated = await update_portfolio_account(test_db, account, cash_balance=90000.0, total_equity=105000.0)
    assert updated.cash_balance == 90000.0
    assert updated.total_equity == 105000.0


@pytest.mark.asyncio
async def test_portfolio_position_lifecycle_crud(test_db: AsyncSession):
    """Verify position entry creation, cash deduction, mark-to-market, and trade exit liquidation."""
    account = await get_or_create_portfolio_account(test_db)
    entry_time = datetime(2026, 11, 1, 9, 30, tzinfo=timezone.utc)

    # 1. Enter position: 100 shares of NVDA at $100.0 ($10,000 total cost)
    pos = await create_portfolio_position(
        db=test_db,
        account_id=account.id,
        ticker="NVDA",
        archetype="The Rocket",
        conviction_score=88.5,
        shares=100,
        entry_price=100.0,
        stop_loss_price=93.0,  # -7%
        target_price=115.0,    # +15%
        entry_date=entry_time,
        spy_entry_price=580.0,
    )
    assert pos.id is not None
    assert pos.status == "OPEN"
    assert pos.ticker == "NVDA"
    assert pos.shares == 100
    assert pos.entry_price == 100.0

    # Account cash should be deducted: 100000 - 10000 = 90000
    acc_check = await get_portfolio_account(test_db, account.id)
    assert acc_check.cash_balance == 90000.0

    # 2. Check open positions list
    open_positions = await get_open_positions(test_db, account.id)
    assert len(open_positions) == 1
    assert open_positions[0].ticker == "NVDA"

    # 3. Mark to market: price rises to $110.0
    pos_updated = await update_open_position_price(test_db, pos, current_price=110.0, holding_days=3)
    assert pos_updated.current_price == 110.0
    assert pos_updated.unrealized_pnl == 1000.0  # (110 - 100) * 100
    assert pos_updated.return_pct == 10.0
    assert pos_updated.holding_days == 3

    # 4. Close position at $116.0 (take-profit hit)
    exit_time = datetime(2026, 11, 6, 16, 0, tzinfo=timezone.utc)
    closed_pos = await close_portfolio_position(
        db=test_db,
        position=pos,
        exit_price=116.0,
        exit_reason="TAKE_PROFIT",
        exit_date=exit_time,
        spy_exit_price=591.6,  # SPY up 2%
    )
    assert closed_pos.status == "CLOSED"
    assert closed_pos.exit_price == 116.0
    assert closed_pos.realized_pnl == 1600.0  # (116 - 100) * 100
    assert closed_pos.unrealized_pnl == 0.0
    assert closed_pos.return_pct == 16.0
    assert closed_pos.exit_reason == "TAKE_PROFIT"
    assert closed_pos.holding_days == 5
    assert closed_pos.spy_return_pct == 2.0
    assert closed_pos.excess_alpha_pct == 14.0  # 16% - 2% = 14%

    # Cash credited back: 90000 + 11600 = 101600
    acc_after = await get_portfolio_account(test_db, account.id)
    assert acc_after.cash_balance == 101600.0

    # Open positions should now be empty
    open_now = await get_open_positions(test_db, account.id)
    assert len(open_now) == 0

    # Closed positions should have 1 record
    closed_list = await get_closed_positions(test_db, account.id)
    assert len(closed_list) == 1
    assert closed_list[0].ticker == "NVDA"


@pytest.mark.asyncio
async def test_portfolio_snapshots_crud(test_db: AsyncSession):
    """Verify daily portfolio equity snapshot recording and retrieval."""
    account = await get_or_create_portfolio_account(test_db)
    now = datetime.now(timezone.utc)

    # Save 2 daily snapshots
    snap1 = await save_portfolio_snapshot(
        db=test_db,
        account_id=account.id,
        snapshot_date=now - timedelta(days=1),
        cash_balance=90000.0,
        invested_capital=10000.0,
        total_equity=100000.0,
        portfolio_return_pct=0.0,
        spy_price=580.0,
        spy_return_pct=0.0,
        excess_alpha_pct=0.0,
        open_positions_count=1,
    )
    assert snap1.id is not None

    snap2 = await save_portfolio_snapshot(
        db=test_db,
        account_id=account.id,
        snapshot_date=now,
        cash_balance=90000.0,
        invested_capital=11500.0,
        total_equity=101500.0,
        portfolio_return_pct=1.5,
        spy_price=585.0,
        spy_return_pct=0.86,
        excess_alpha_pct=0.64,
        open_positions_count=1,
    )
    assert snap2.id is not None

    snapshots = await get_portfolio_snapshots(test_db, account.id)
    assert len(snapshots) == 2
    assert snapshots[0].total_equity == 100000.0
    assert snapshots[1].total_equity == 101500.0

    latest = await get_latest_portfolio_snapshot(test_db, account.id)
    assert latest is not None
    assert latest.id == snap2.id
    assert latest.total_equity == 101500.0

