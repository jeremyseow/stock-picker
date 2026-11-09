import pytest
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone

from app.main import app
from app.database import get_db, Base
from app.models import PortfolioAccount, PortfolioPosition, PortfolioSnapshot, SynthesisReport
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


@pytest.mark.asyncio
async def test_portfolio_summary_and_positions_api(client: AsyncClient, test_db: AsyncSession):
    """Verify /api/portfolio/summary and /api/portfolio/positions endpoints."""
    # 1. Summary endpoint should initialize and return $100k account
    res = await client.get("/api/portfolio/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["initial_balance"] == 100000.0
    assert data["cash_balance"] == 100000.0
    assert data["total_equity"] == 100000.0
    assert data["open_positions_count"] == 0

    # 2. Add an open position directly to DB
    account_id = data["account_id"]
    pos = PortfolioPosition(
        account_id=account_id,
        ticker="AAPL",
        archetype="Silent Accumulation",
        conviction_score=82.0,
        status="OPEN",
        shares=50,
        entry_date=datetime(2026, 11, 2, 9, 30, tzinfo=timezone.utc),
        entry_price=180.0,
        current_price=185.0,
        stop_loss_price=167.4,
        target_price=207.0,
        unrealized_pnl=250.0,
        return_pct=2.78,
        holding_days=3,
    )
    test_db.add(pos)
    await test_db.commit()
    await test_db.refresh(pos)

    # 3. Query positions endpoint
    pos_res = await client.get("/api/portfolio/positions")
    assert pos_res.status_code == 200
    pos_data = pos_res.json()
    assert len(pos_data) == 1
    assert pos_data[0]["ticker"] == "AAPL"
    assert pos_data[0]["unrealized_pnl"] == 250.0
    assert pos_data[0]["status"] == "OPEN"


@pytest.mark.asyncio
async def test_manual_close_and_journal_api(client: AsyncClient, test_db: AsyncSession):
    """Verify manual position closing and trade journal retrieval via API."""
    sum_res = await client.get("/api/portfolio/summary")
    account_id = sum_res.json()["account_id"]

    pos = PortfolioPosition(
        account_id=account_id,
        ticker="NVDA",
        archetype="The Rocket",
        conviction_score=91.0,
        status="OPEN",
        shares=100,
        entry_date=datetime(2026, 11, 1, 9, 30, tzinfo=timezone.utc),
        entry_price=120.0,
        current_price=130.0,
        stop_loss_price=111.6,
        target_price=140.0,
        spy_entry_price=580.0,
    )
    test_db.add(pos)
    await test_db.commit()
    await test_db.refresh(pos)

    # 1. Close position via API
    close_res = await client.post(f"/api/portfolio/positions/{pos.id}/close")
    assert close_res.status_code == 200
    close_data = close_res.json()
    assert close_data["status"] == "success"
    assert close_data["position"]["exit_reason"] == "MANUAL"
    assert close_data["position"]["status"] == "CLOSED"

    # 2. Attempting to close an already-closed position should return 400 Bad Request
    err_res = await client.post(f"/api/portfolio/positions/{pos.id}/close")
    assert err_res.status_code == 400
    assert "already CLOSED" in err_res.json()["detail"]

    # 3. Check trade journal
    journal_res = await client.get("/api/portfolio/journal")
    assert journal_res.status_code == 200
    journal_data = journal_res.json()
    assert len(journal_data) == 1
    assert journal_data[0]["ticker"] == "NVDA"
    assert journal_data[0]["exit_reason"] == "MANUAL"


@pytest.mark.asyncio
async def test_portfolio_snapshots_api(client: AsyncClient, test_db: AsyncSession):
    """Verify /api/portfolio/snapshots endpoint."""
    sum_res = await client.get("/api/portfolio/summary")
    account_id = sum_res.json()["account_id"]

    snap = PortfolioSnapshot(
        account_id=account_id,
        snapshot_date=datetime(2026, 11, 5, 16, 0, tzinfo=timezone.utc),
        cash_balance=85000.0,
        invested_capital=16000.0,
        total_equity=101000.0,
        portfolio_return_pct=1.0,
        spy_price=585.0,
        spy_return_pct=0.5,
        excess_alpha_pct=0.5,
        open_positions_count=2,
    )
    test_db.add(snap)
    await test_db.commit()

    res = await client.get("/api/portfolio/snapshots")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["total_equity"] == 101000.0
    assert data[0]["excess_alpha_pct"] == 0.5

