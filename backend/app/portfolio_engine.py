import logging
import math
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
import yfinance as yf
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from app.models import (
    PortfolioAccount,
    PortfolioPosition,
    PortfolioSnapshot,
    SynthesisReport,
    ModelCalibrationRun,
)
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
    get_latest_synthesis_reports,
    get_synthesis_reports_by_date,
)

logger = logging.getLogger(__name__)

# Portfolio Parameters
INITIAL_CAPITAL = 100000.0
POSITION_ALLOCATION = 10000.0  # $10,000 per position (10%)
MAX_CONCURRENT_POSITIONS = 10
# Archetype Risk/Reward Brackets
ARCHETYPE_RISK_BRACKETS = {
    "The Rocket": {
        "stop_loss_pct": 0.05,        # -5.0% fast cut on stalled momentum
        "take_profit_pct": 0.12,      # +12.0% realistic burst target
        "horizon_days": 8,            # 8 trading days
    },
    "Silent Accumulation": {
        "stop_loss_pct": 0.08,        # -8.0% room for base consolidation
        "take_profit_pct": 0.20,      # +20.0% institutional accumulation swing
        "horizon_days": 22,           # 22 trading days
    },
}
DEFAULT_STOP_LOSS_PCT = 0.07
DEFAULT_TAKE_PROFIT_PCT = 0.15
COOLOFF_DAYS_AFTER_STOP = 7    # 7-day post-stop-loss lockout to prevent wash-sale churn

def get_archetype_risk_brackets(archetype: str) -> tuple[float, float]:
    """Retrieve calibrated stop-loss and take-profit percentages by archetype."""
    bracket = ARCHETYPE_RISK_BRACKETS.get(archetype, {})
    stop_pct = bracket.get("stop_loss_pct", DEFAULT_STOP_LOSS_PCT)
    tp_pct = bracket.get("take_profit_pct", DEFAULT_TAKE_PROFIT_PCT)
    return stop_pct, tp_pct

# Quant Priors for Maturation Horizon (trading days)
ROCKET_HOLDING_DAYS_PRIOR = 8
SILENT_ACCUMULATION_HOLDING_DAYS_PRIOR = 22
DEFAULT_HOLDING_DAYS_PRIOR = 15

QUALIFYING_ARCHETYPES = {"The Rocket", "Silent Accumulation"}
MIN_CONVICTION_SCORE = 75.0
SPY_TICKER = "SPY"


def fetch_ticker_price(
    ticker: str, price_type: str = "current", target_date: Optional[str] = None
) -> Optional[float]:
    """
    Fetch price for a ticker via yfinance.
    price_type: 'open', 'close', or 'current'.
    target_date: Optional YYYY-MM-DD for historical queries.
    """
    try:
        t = yf.Ticker(ticker)

        # Historical backfill lookup
        if target_date:
            try:
                start_dt = datetime.strptime(target_date, "%Y-%m-%d")
                end_dt = start_dt + timedelta(days=5)
                hist = t.history(start=start_dt.strftime("%Y-%m-%d"), end=end_dt.strftime("%Y-%m-%d"))
                if not hist.empty:
                    row = hist.iloc[0]
                    if price_type == "open" and "Open" in row and not math.isnan(row["Open"]):
                        return float(row["Open"])
                    if "Close" in row and not math.isnan(row["Close"]):
                        return float(row["Close"])
            except Exception as e:
                logger.warning(f"Error fetching historical price for {ticker} on {target_date}: {e}")

        # Live / current price path
        if price_type == "current":
            last_price = getattr(t.fast_info, "last_price", None) or getattr(t.fast_info, "previous_close", None)
            if last_price and not math.isnan(last_price) and last_price > 0:
                return float(last_price)

        # 5-day history for recent open/close bars
        hist = t.history(period="5d")
        if not hist.empty:
            last_row = hist.iloc[-1]
            if price_type == "open" and "Open" in last_row and not math.isnan(last_row["Open"]):
                return float(last_row["Open"])
            if "Close" in last_row and not math.isnan(last_row["Close"]):
                return float(last_row["Close"])

        return None
    except Exception as exc:
        logger.warning(f"Failed to fetch {price_type} price for {ticker}: {exc}")
        return None


async def get_archetype_holding_horizon(db: AsyncSession, archetype: str) -> int:
    """
    Calculate dynamic holding horizon:
    - If archetype closed trades < 15: use quant prior.
    - If cohort >= 15: apply Bayesian blend with empirical calibration duration.
    """
    prior = (
        ROCKET_HOLDING_DAYS_PRIOR
        if archetype == "The Rocket"
        else SILENT_ACCUMULATION_HOLDING_DAYS_PRIOR
        if archetype == "Silent Accumulation"
        else DEFAULT_HOLDING_DAYS_PRIOR
    )

    # Count closed trades in this archetype
    query = (
        select(PortfolioPosition)
        .where(PortfolioPosition.status == "CLOSED", PortfolioPosition.archetype == archetype)
    )
    res = await db.execute(query)
    closed = list(res.scalars().all())

    if len(closed) < 15:
        return prior

    # Empirical median holding days of profitable trades
    profitable_days = [p.holding_days for p in closed if p.holding_days and (p.realized_pnl or 0) > 0]
    if not profitable_days:
        return prior

    profitable_days.sort()
    emp_median = profitable_days[len(profitable_days) // 2]

    # Bayesian blend: weight prior by 15, empirical by (N - 15)
    weight_prior = 15.0
    weight_emp = float(len(closed) - 15)
    blended = (prior * weight_prior + emp_median * weight_emp) / (weight_prior + weight_emp)
    return max(5, min(30, int(round(blended))))


async def qualify_synthesis_signals(
    db: AsyncSession, date_str: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Extract eligible trade entry candidates from the synthesis reports.
    Requirements:
    - Archetype in ('The Rocket', 'Silent Accumulation')
    - Overall score >= 75.0
    - Not already in open positions
    """
    if date_str:
        reports = await get_synthesis_reports_by_date(db, date_str)
    else:
        reports = await get_latest_synthesis_reports(db)

    if not reports:
        return []
    open_positions = await get_open_positions(db)
    open_tickers = {p.ticker.upper() for p in open_positions}

    # Reference date for post-stop cool-off lockout
    if date_str:
        try:
            ref_dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except Exception:
            ref_dt = datetime.now(timezone.utc)
    else:
        ref_dt = datetime.now(timezone.utc)

    # Lockout tickers that suffered a STOP_LOSS exit within the last 7 days
    cooloff_threshold = ref_dt - timedelta(days=COOLOFF_DAYS_AFTER_STOP)
    cooloff_query = (
        select(PortfolioPosition.ticker)
        .where(
            PortfolioPosition.status == "CLOSED",
            PortfolioPosition.exit_reason == "STOP_LOSS",
            PortfolioPosition.exit_date >= cooloff_threshold,
            PortfolioPosition.exit_date <= ref_dt,
        )
    )
    cooloff_res = await db.execute(cooloff_query)
    cooloff_tickers = {row[0].upper() for row in cooloff_res.all() if row[0]}

    candidates = []
    for r in reports:
        sym = r.ticker.upper()
        if sym in open_tickers:
            continue
        if sym in cooloff_tickers:
            logger.info(f"Skipping {sym}: Under {COOLOFF_DAYS_AFTER_STOP}-day post-stop cool-off lockout.")
            continue
        score = float(r.timing_edge_score or 0.0)
        if r.archetype in QUALIFYING_ARCHETYPES and score >= MIN_CONVICTION_SCORE:
            target_pr = getattr(r, "target_price", None)
            candidates.append({
                "ticker": sym,
                "archetype": r.archetype,
                "overall_score": score,
                "target_price": float(target_pr) if target_pr else None,
                "date": date_str,
            })

    # Sort descending by overall conviction score
    candidates.sort(key=lambda x: x["overall_score"], reverse=True)
    return candidates


async def execute_market_open_orders(
    db: AsyncSession,
    date_str: Optional[str] = None,
    mock_prices: Optional[Dict[str, float]] = None,
    mock_spy_price: Optional[float] = None,
) -> Dict[str, Any]:
    """
    US Market Open (09:30 ET) Execution Job:
    1. Fetches candidate signals.
    2. Enforces $10k fixed allocation per position, max 10 concurrent slots (queue discipline A).
    3. Fills at real market open price via yfinance.
    4. Sets stop-loss (-7%) and take-profit target (+15%).
    """
    account = await get_or_create_portfolio_account(db)
    open_positions = await get_open_positions(db, account.id)

    available_slots = MAX_CONCURRENT_POSITIONS - len(open_positions)
    if available_slots <= 0:
        logger.info(f"Market open execution: Portfolio at max capacity ({len(open_positions)}/10 slots). Skipping.")
        return {
            "status": "full",
            "message": "Max concurrent positions reached (10/10)",
            "executed": [],
            "skipped": [],
        }

    candidates = await qualify_synthesis_signals(db, date_str)
    if not candidates:
        logger.info("Market open execution: No eligible candidate signals found.")
        return {
            "status": "no_signals",
            "message": "No qualifying signals found",
            "executed": [],
            "skipped": [],
        }

    # Fetch SPY benchmark price
    target_date = date_str if date_str else None
    spy_price = (
        mock_spy_price
        if mock_spy_price is not None
        else fetch_ticker_price(SPY_TICKER, "open", target_date=target_date)
        or fetch_ticker_price(SPY_TICKER, "current")
    )

    executed = []
    skipped = []

    for candidate in candidates:
        if available_slots <= 0:
            skipped.append({"ticker": candidate["ticker"], "reason": "capacity_full"})
            continue

        if account.cash_balance < POSITION_ALLOCATION:
            skipped.append({"ticker": candidate["ticker"], "reason": "insufficient_cash"})
            continue

        sym = candidate["ticker"]
        # Determine entry open price
        if mock_prices and sym in mock_prices:
            open_price = mock_prices[sym]
        else:
            open_price = fetch_ticker_price(sym, "open", target_date=target_date) or fetch_ticker_price(sym, "current")

        if not open_price or open_price <= 0:
            skipped.append({"ticker": sym, "reason": "price_unavailable"})
            continue

        shares = int(POSITION_ALLOCATION // open_price)
        if shares <= 0:
            skipped.append({"ticker": sym, "reason": "share_allocation_zero"})
            continue

        stop_pct, tp_pct = get_archetype_risk_brackets(candidate["archetype"])
        stop_loss_price = round(open_price * (1.0 - stop_pct), 2)
        base_take_profit = round(open_price * (1.0 + tp_pct), 2)
        target_price = candidate.get("target_price")
        # If research target price is significantly higher, use it, otherwise default to +15%
        if target_price and target_price > base_take_profit:
            take_profit_price = round(target_price, 2)
        else:
            take_profit_price = base_take_profit

        if date_str:
            try:
                entry_date = datetime.strptime(date_str, "%Y-%m-%d").replace(hour=9, minute=30, tzinfo=timezone.utc)
            except Exception:
                entry_date = datetime.now(timezone.utc)
        else:
            entry_date = datetime.now(timezone.utc)

        pos = await create_portfolio_position(
            db=db,
            account_id=account.id,
            ticker=sym,
            archetype=candidate["archetype"],
            conviction_score=candidate["overall_score"],
            shares=shares,
            entry_price=round(open_price, 2),
            stop_loss_price=stop_loss_price,
            target_price=take_profit_price,
            entry_date=entry_date,
            spy_entry_price=round(spy_price, 2) if spy_price else None,
        )

        available_slots -= 1
        account = await get_portfolio_account(db, account.id)  # refresh cash balance
        executed.append({
            "position_id": pos.id,
            "ticker": sym,
            "shares": shares,
            "entry_price": pos.entry_price,
            "stop_loss": pos.stop_loss_price,
            "target_price": pos.target_price,
        })

    return {
        "status": "success",
        "executed_count": len(executed),
        "executed": executed,
        "skipped": skipped,
        "remaining_cash": account.cash_balance,
    }


async def evaluate_market_close_exits(
    db: AsyncSession,
    mock_prices: Optional[Dict[str, float]] = None,
    mock_spy_price: Optional[float] = None,
    exit_date: Optional[datetime] = None,
    date_str: Optional[str] = None,
) -> Dict[str, Any]:
    """
    US Market Close (16:00 ET) Exit Evaluation & Mark-to-Market Job:
    1. Hard Stop-Loss: return <= -7.0% -> Exit STOP_LOSS
    2. Take-Profit Target: return >= +15.0% or current_price >= target_price -> Exit TAKE_PROFIT
    3. Time-decay: holding_days >= archetype max horizon -> Exit TIME_EXIT
    4. Otherwise: Stay OPEN, update unrealized PnL and current price.
    """
    account = await get_or_create_portfolio_account(db)
    open_positions = await get_open_positions(db, account.id)
    if not open_positions:
        return {"status": "no_open_positions", "closed_positions": [], "updated_positions": []}

    target_date = date_str if date_str else None
    if exit_date:
        eval_dt = exit_date
    elif date_str:
        try:
            eval_dt = datetime.strptime(date_str, "%Y-%m-%d").replace(hour=16, minute=0, tzinfo=timezone.utc)
        except Exception:
            eval_dt = datetime.now(timezone.utc)
    else:
        eval_dt = datetime.now(timezone.utc)

    # Fetch SPY closing benchmark price
    spy_price = (
        mock_spy_price
        if mock_spy_price is not None
        else fetch_ticker_price(SPY_TICKER, "close", target_date=target_date)
        or fetch_ticker_price(SPY_TICKER, "current")
    )

    closed_positions = []
    updated_positions = []

    for pos in open_positions:
        sym = pos.ticker
        if mock_prices and sym in mock_prices:
            close_price = mock_prices[sym]
        else:
            close_price = (
                fetch_ticker_price(sym, "close", target_date=target_date)
                or fetch_ticker_price(sym, "current")
            )

        if not close_price or close_price <= 0:
            logger.warning(f"Could not retrieve close price for {sym}, skipping evaluation.")
            continue

        # Increment holding days
        days = (eval_dt.date() - pos.entry_date.date()).days
        holding_days = max(1, days)
        horizon = await get_archetype_holding_horizon(db, pos.archetype)

        ret_pct = ((close_price - pos.entry_price) / pos.entry_price) * 100.0

        stop_pct, tp_pct = get_archetype_risk_brackets(pos.archetype)

        # Check exit conditions in order of precedence:
        exit_reason = None
        if close_price <= pos.stop_loss_price or ret_pct <= -(stop_pct * 100.0):
            exit_reason = "STOP_LOSS"
        elif (pos.target_price and close_price >= pos.target_price) or ret_pct >= (tp_pct * 100.0):
            exit_reason = "TAKE_PROFIT"
        elif holding_days >= horizon:
            exit_reason = "TIME_EXIT"

        if exit_reason:
            closed = await close_portfolio_position(
                db=db,
                position=pos,
                exit_price=round(close_price, 2),
                exit_reason=exit_reason,
                exit_date=eval_dt,
                spy_exit_price=round(spy_price, 2) if spy_price else None,
            )
            closed_positions.append({
                "position_id": closed.id,
                "ticker": closed.ticker,
                "exit_reason": closed.exit_reason,
                "exit_price": closed.exit_price,
                "realized_pnl": closed.realized_pnl,
                "return_pct": closed.return_pct,
                "excess_alpha_pct": closed.excess_alpha_pct,
            })
        else:
            updated = await update_open_position_price(
                db=db,
                position=pos,
                current_price=close_price,
                holding_days=holding_days,
            )
            updated_positions.append({
                "position_id": updated.id,
                "ticker": updated.ticker,
                "current_price": updated.current_price,
                "unrealized_pnl": updated.unrealized_pnl,
                "return_pct": updated.return_pct,
                "holding_days": updated.holding_days,
            })

    # Record daily snapshot after close evaluation
    snapshot = await record_daily_portfolio_snapshot(db, account.id, eval_dt, spy_price)

    return {
        "status": "success",
        "closed_count": len(closed_positions),
        "closed_positions": closed_positions,
        "updated_count": len(updated_positions),
        "updated_positions": updated_positions,
        "snapshot_total_equity": snapshot.total_equity,
    }


async def close_position_manually(
    db: AsyncSession,
    position_id: int,
    mock_price: Optional[float] = None,
    mock_spy_price: Optional[float] = None,
) -> PortfolioPosition:
    """Manual liquidation override invoked by user."""
    pos = await get_position_by_id(db, position_id)
    if not pos:
        raise ValueError(f"Position {position_id} not found.")
    if pos.status != "OPEN":
        raise ValueError(f"Position {position_id} is already CLOSED.")

    if mock_price is not None:
        exit_price = mock_price
    else:
        exit_price = fetch_ticker_price(pos.ticker, "current") or pos.current_price or pos.entry_price

    if not exit_price or exit_price <= 0:
        raise ValueError(f"Cannot retrieve valid market price for {pos.ticker}")

    spy_price = mock_spy_price if mock_spy_price is not None else fetch_ticker_price(SPY_TICKER, "current")

    closed = await close_portfolio_position(
        db=db,
        position=pos,
        exit_price=round(exit_price, 2),
        exit_reason="MANUAL",
        exit_date=datetime.now(timezone.utc),
        spy_exit_price=round(spy_price, 2) if spy_price else None,
    )
    return closed


async def record_daily_portfolio_snapshot(
    db: AsyncSession,
    account_id: int,
    snapshot_date: Optional[datetime] = None,
    current_spy_price: Optional[float] = None,
) -> PortfolioSnapshot:
    """Calculate aggregate portfolio equity and log daily snapshot."""
    dt = snapshot_date or datetime.now(timezone.utc)
    account = await get_portfolio_account(db, account_id)
    if not account:
        account = await get_or_create_portfolio_account(db)

    open_positions = await get_open_positions(db, account.id)
    invested_capital = sum(
        p.shares * (p.current_price or p.entry_price) for p in open_positions
    )
    total_equity = round(account.cash_balance + invested_capital, 2)

    # Update account total equity
    await update_portfolio_account(db, account, total_equity=total_equity)

    portfolio_return_pct = round(
        ((total_equity - account.initial_balance) / account.initial_balance) * 100.0, 2
    )

    # SPY benchmark comparison
    spy_price = current_spy_price
    if spy_price is None:
        spy_price = fetch_ticker_price(SPY_TICKER, "current")

    # Fetch earliest snapshot to establish SPY baseline
    first_snap_query = (
        select(PortfolioSnapshot)
        .where(PortfolioSnapshot.account_id == account.id, PortfolioSnapshot.spy_price.isnot(None))
        .order_by(PortfolioSnapshot.snapshot_date.asc())
        .limit(1)
    )
    first_snap_res = await db.execute(first_snap_query)
    first_snap = first_snap_res.scalar_one_or_none()

    spy_return_pct = 0.0
    excess_alpha_pct = portfolio_return_pct
    if first_snap and first_snap.spy_price and spy_price and first_snap.spy_price > 0:
        spy_return_pct = round(
            ((spy_price - first_snap.spy_price) / first_snap.spy_price) * 100.0, 2
        )
        excess_alpha_pct = round(portfolio_return_pct - spy_return_pct, 2)

    snapshot = await save_portfolio_snapshot(
        db=db,
        account_id=account.id,
        snapshot_date=dt,
        cash_balance=account.cash_balance,
        invested_capital=invested_capital,
        total_equity=total_equity,
        portfolio_return_pct=portfolio_return_pct,
        spy_price=spy_price,
        spy_return_pct=spy_return_pct,
        excess_alpha_pct=excess_alpha_pct,
        open_positions_count=len(open_positions),
    )
    return snapshot


async def get_portfolio_summary_metrics(db: AsyncSession) -> Dict[str, Any]:
    """Calculate summary KPI metrics for the /portfolio dashboard header."""
    account = await get_or_create_portfolio_account(db)
    open_positions = await get_open_positions(db, account.id)
    closed_positions = await get_closed_positions(db, account.id, limit=500)
    latest_snapshot = await get_latest_portfolio_snapshot(db, account.id)

    invested_capital = sum(
        p.shares * (p.current_price or p.entry_price) for p in open_positions
    )
    total_equity = round(account.cash_balance + invested_capital, 2)
    total_return_dollar = round(total_equity - account.initial_balance, 2)
    total_return_pct = round((total_return_dollar / account.initial_balance) * 100.0, 2)

    # Win rate and realized PnL
    profitable_trades = [p for p in closed_positions if (p.realized_pnl or 0) > 0]
    total_closed = len(closed_positions)
    win_rate = round((len(profitable_trades) / total_closed) * 100.0, 1) if total_closed > 0 else 0.0
    total_realized_pnl = round(sum(p.realized_pnl or 0.0 for p in closed_positions), 2)
    total_unrealized_pnl = round(sum(p.unrealized_pnl or 0.0 for p in open_positions), 2)

    # Cumulative excess alpha vs SPY across closed trades
    excess_alpha_pct = latest_snapshot.excess_alpha_pct if latest_snapshot else total_return_pct

    return {
        "account_id": account.id,
        "name": account.name,
        "initial_balance": account.initial_balance,
        "cash_balance": account.cash_balance,
        "invested_capital": round(invested_capital, 2),
        "total_equity": total_equity,
        "total_return_dollar": total_return_dollar,
        "total_return_pct": total_return_pct,
        "total_realized_pnl": total_realized_pnl,
        "total_unrealized_pnl": total_unrealized_pnl,
        "open_positions_count": len(open_positions),
        "max_positions": MAX_CONCURRENT_POSITIONS,
        "closed_trades_count": total_closed,
        "win_rate_pct": win_rate,
        "excess_alpha_pct": excess_alpha_pct,
    }


async def bootstrap_portfolio_history(
    db: AsyncSession, reset: bool = True
) -> Dict[str, Any]:
    """
    Simulate paper trading portfolio over all existing historical synthesis reports.
    Iterates chronologically by date, executes open orders, marks exits, and builds daily snapshots.
    """
    account = await get_or_create_portfolio_account(db)

    if reset:
        # Clear existing positions and snapshots for clean historical simulation
        await db.execute(select(PortfolioPosition))
        del_pos = PortfolioPosition.__table__.delete().where(PortfolioPosition.account_id == account.id)
        del_snap = PortfolioSnapshot.__table__.delete().where(PortfolioSnapshot.account_id == account.id)
        await db.execute(del_pos)
        await db.execute(del_snap)
        account.cash_balance = account.initial_balance
        account.total_equity = account.initial_balance
        await db.commit()

    # Query all unique synthesis report dates sorted ascending
    query = (
        select(SynthesisReport.date)
        .distinct()
        .order_by(SynthesisReport.date.asc())
    )
    result = await db.execute(query)
    dates = [row[0] for row in result.all() if row[0]]

    if not dates:
        return {"status": "no_historical_data", "dates_processed": 0}

    # Group unique dates by YYYY-MM-DD
    unique_date_strs = sorted(list({d.strftime("%Y-%m-%d") for d in dates}))

    simulated_orders = 0
    simulated_exits = 0

    for d_str in unique_date_strs:
        # Step 1: Market Open Execution on historical date
        open_res = await execute_market_open_orders(db, date_str=d_str)
        simulated_orders += open_res.get("executed_count", 0)

        # Step 2: Market Close Exit Evaluation on historical date
        close_res = await evaluate_market_close_exits(db, date_str=d_str)
        simulated_exits += close_res.get("closed_count", 0)

    # Finally, for any positions that remain open after all historical dates,
    # mark them to market using TODAY's live price and accurate elapsed holding days
    today_dt = datetime.now(timezone.utc)
    open_now = await get_open_positions(db, account.id)
    for p in open_now:
        live_price = fetch_ticker_price(p.ticker, "current")
        if live_price and live_price > 0:
            days = (today_dt.date() - p.entry_date.date()).days
            await update_open_position_price(db, p, current_price=live_price, holding_days=max(1, days))

    # Record the final snapshot as of today
    await record_daily_portfolio_snapshot(db, account.id)

    metrics = await get_portfolio_summary_metrics(db)
    return {
        "status": "success",
        "dates_processed": len(unique_date_strs),
        "orders_executed": simulated_orders,
        "positions_closed": simulated_exits,
        "final_metrics": metrics,
    }
