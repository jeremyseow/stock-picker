import asyncio
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.database import AsyncSessionLocal, init_db
from app.portfolio_engine import bootstrap_portfolio_history, get_portfolio_summary_metrics


async def main():
    print("Initializing database...")
    await init_db()
    async with AsyncSessionLocal() as session:
        print("Executing portfolio historical bootstrap simulation...")
        res = await bootstrap_portfolio_history(session, reset=True)
        print(f"Bootstrap Status: {res.get('status')}")
        print(f"Dates processed: {res.get('dates_processed')}")
        print(f"Orders executed: {res.get('orders_executed')}")
        print(f"Positions closed: {res.get('positions_closed')}")
        metrics = await get_portfolio_summary_metrics(session)
        print("\n=== Live Portfolio Summary ===")
        print(f"Total Equity: ${metrics['total_equity']:,.2f}")
        print(f"Cash Balance: ${metrics['cash_balance']:,.2f}")
        print(f"Invested Capital: ${metrics['invested_capital']:,.2f}")
        print(f"Total Return: {metrics['total_return_pct']:+.2f}% (${metrics['total_return_dollar']:+,.2f})")
        print(f"Win Rate: {metrics['win_rate_pct']:.1f}%")
        print(f"Excess Alpha vs SPY: {metrics['excess_alpha_pct']:+.2f}%")
        print(f"Active Positions: {metrics['open_positions_count']}/{metrics['max_positions']}")
        print(f"Closed Trades: {metrics['closed_trades_count']}")


if __name__ == "__main__":
    asyncio.run(main())

