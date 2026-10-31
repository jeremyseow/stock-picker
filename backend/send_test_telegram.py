import asyncio
import logging
from dotenv import load_dotenv

load_dotenv()

from app.database import AsyncSessionLocal, init_db
from app.crud import get_reports_by_date, get_distinct_report_dates
from app.telegram_notifier import send_daily_digest

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

async def main():
    await init_db()
    async with AsyncSessionLocal() as db:
        dates = await get_distinct_report_dates(db)
        if not dates:
            print("❌ No historical reports found in database to send.")
            return

        latest_date = dates[0]
        reports = await get_reports_by_date(db, latest_date)
        print(f"Found {len(reports)} reports from latest date ({latest_date}). Formatting digest...")

        summaries = []
        for i, r in enumerate(reports, 1):
            summaries.append({
                "rank": i,
                "ticker": r.ticker,
                "recommendation": r.recommendation,
                "current_price": r.current_price,
                "target_price": r.target_price,
                "smart_money_verdict": r.smart_money_verdict,
                "actionable_insight": r.reconciliation_actionable_insight
            })

        print("Dispatching digest to Telegram...")
        success = await send_daily_digest(summaries)
        if success:
            print("[SUCCESS] Telegram notification delivered successfully! Check your Telegram chat.")
        else:
            print("[FAILED] Failed to send Telegram message. Please check your TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in backend/.env.")

if __name__ == "__main__":
    asyncio.run(main())
