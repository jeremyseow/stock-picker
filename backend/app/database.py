from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from pathlib import Path
import os

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "stock_analyzer.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{DEFAULT_DB_PATH.as_posix()}")

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    import app.models  # Ensure models are registered on metadata
    async with engine.begin() as conn:
        # Create tables
        await conn.run_sync(Base.metadata.create_all)

        # Self-healing column migrations for existing SQLite tables
        def migrate_columns(sync_conn):
            rows_rep = sync_conn.exec_driver_sql("PRAGMA table_info(synthesis_reports)").fetchall()
            if rows_rep:
                existing_rep_cols = {r[1] for r in rows_rep}
                if "whale_options_flow" not in existing_rep_cols:
                    sync_conn.exec_driver_sql("ALTER TABLE synthesis_reports ADD COLUMN whale_options_flow VARCHAR")
                if "whale_options_score" not in existing_rep_cols:
                    sync_conn.exec_driver_sql("ALTER TABLE synthesis_reports ADD COLUMN whale_options_score FLOAT DEFAULT 0.0")
                if "put_call_ratio" not in existing_rep_cols:
                    sync_conn.exec_driver_sql("ALTER TABLE synthesis_reports ADD COLUMN put_call_ratio FLOAT")

        await conn.run_sync(migrate_columns)
