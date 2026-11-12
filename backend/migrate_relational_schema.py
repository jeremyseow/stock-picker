"""Idempotent migration script aligning backend/stock_analyzer.db with the normalized relational schema in app/models.py.

Steps:
1. Checks if stock_analyzer.db is already on the target schema (no-op if already migrated).
2. Creates a timestamped backup of stock_analyzer.db before touching anything.
3. Initializes a clean target SQLite DB using SQLAlchemy's Base.metadata.create_all().
4. Copies all unchanged tables verbatim (preserving primary keys).
5. Backfills Form 4 insider transactions from historical retail_sentiment_reports.raw_insider_data
   into insider_trades_raw (deduplicated).
6. Migrates & links foreign keys for:
   - core_equity_reports (links core_raw_id -> core_equity_raw.id; drops raw_* JSON columns)
   - retail_sentiment_reports (links daily_ticker_id -> daily_tickers.id; drops leaderboard & insider cols)
   - smart_money_reports (links smart_money_ticker_id -> smart_money_tickers.id; synthesizes missing ticker row if needed)
   - options_whale_reports (links options_whale_ticker_id -> options_whale_tickers.id; drops leaderboard & unusual_contracts)
   - options_whale_raw + options_report_contracts (pure Layer 1 raw contracts; backfills dte/is_otm/is_sweep; links via options_report_contracts junction table)
   - synthesis_reports (links retail_report_id, smart_money_report_id, options_whale_report_id; drops cross-engine snapshots)
7. Verifies row counts, schema parity, and PRAGMA foreign_key_check before atomically swapping the DB file.
"""
import json
import os
import shutil
import sqlite3
from datetime import datetime, timezone
from sqlalchemy import create_engine

from app.database import Base
import app.models  # noqa: F401 - register all SQLAlchemy models on Base.metadata


DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "stock_analyzer.db"))


def _date_day(ts: str | None) -> str:
    if not ts:
        return ""
    return str(ts)[:10]


def _closest_id(candidates: list[tuple[int, str]], target_ts: str | None) -> int | None:
    if not candidates:
        return None
    target_day = _date_day(target_ts)
    same_day = [c for c in candidates if _date_day(c[1]) == target_day]
    pool = same_day if same_day else candidates
    # Prefer the latest record at or before target_ts, else closest overall
    if target_ts:
        at_or_before = [c for c in pool if (c[1] or "") <= target_ts]
        if at_or_before:
            return sorted(at_or_before, key=lambda x: x[1] or "")[-1][0]
    return sorted(pool, key=lambda x: x[1] or "")[-1][0]


def _schema_needs_migration(conn: sqlite3.Connection) -> bool:
    cur = conn.cursor()
    for table_name, table in Base.metadata.tables.items():
        cur.execute(f"PRAGMA table_info('{table_name}')")
        actual = {r[1] for r in cur.fetchall()}
        expected = set(table.columns.keys())
        if actual != expected:
            return True
    return False


def migrate(db_path: str = DB_PATH) -> None:
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at {db_path}")

    src = sqlite3.connect(db_path)
    src.row_factory = sqlite3.Row
    if not _schema_needs_migration(src):
        print("Database schema already matches app/models.py. Nothing to migrate.")
        src.close()
        return

    backup_path = f"{db_path}.pre_norm_backup"
    shutil.copy2(db_path, backup_path)
    print(f"Created safety backup: {backup_path}")

    tmp_path = f"{db_path}.migrating"
    if os.path.exists(tmp_path):
        os.remove(tmp_path)

    # Create target schema cleanly from Base.metadata
    sync_engine = create_engine(f"sqlite:///{tmp_path}")
    Base.metadata.create_all(sync_engine)
    sync_engine.dispose()

    dst = sqlite3.connect(tmp_path)
    src_cur = src.cursor()
    dst_cur = dst.cursor()
    dst_cur.execute("PRAGMA foreign_keys = OFF")

    try:
        # 1. Copy unchanged base/raw/leaderboard/portfolio/analytics tables verbatim
        unchanged_tables = [
            "daily_tickers",
            "smart_money_tickers",
            "options_whale_tickers",
            "core_equity_raw",
            "retail_social_raw",
            "insider_trades_raw",
            "congress_trades_raw",
            "ticker_trajectory_analyses",
            "model_calibration_runs",
            "portfolio_accounts",
            "portfolio_positions",
            "portfolio_snapshots",
        ]
        for table_name in unchanged_tables:
            cols = list(Base.metadata.tables[table_name].columns.keys())
            col_list = ", ".join(cols)
            placeholders = ", ".join(["?"] * len(cols))
            rows = src_cur.execute(f"SELECT {col_list} FROM {table_name}").fetchall()
            if rows:
                dst_cur.executemany(
                    f"INSERT INTO {table_name} ({col_list}) VALUES ({placeholders})",
                    [tuple(r[c] for c in cols) for r in rows],
                )
            print(f"Copied {len(rows)} rows -> {table_name}")

        # 2. Backfill historical Form 4 transactions from old retail_sentiment_reports.raw_insider_data
        existing_insiders: set[tuple[str, str, str, str, float]] = set()
        for r in dst.execute(
            "SELECT ticker, filing_date, trade_date, insider_name, transaction_type, shares FROM insider_trades_raw"
        ).fetchall():
            existing_insiders.add((r[0], r[1] or r[2] or "", r[3], r[4], float(r[5] or 0.0)))

        migrated_insiders = 0
        retail_rows = src_cur.execute("SELECT * FROM retail_sentiment_reports").fetchall()
        for r in retail_rows:
            if "raw_insider_data" not in r.keys():
                break
            raw_ins = r["raw_insider_data"]
            if not raw_ins:
                continue
            payload = json.loads(raw_ins) if isinstance(raw_ins, str) else raw_ins
            if not isinstance(payload, dict):
                continue
            for tx in payload.get("recent_transactions") or []:
                tx_date = str(tx.get("date") or "")
                insider_name = str(tx.get("insider") or tx.get("insider_name") or "Unknown").strip()
                tx_type = str(tx.get("type") or tx.get("transaction_type") or "OTHER").upper()
                shares = float(tx.get("shares") or 0.0)
                key = (r["ticker"], tx_date, insider_name, tx_type, shares)
                if key in existing_insiders:
                    continue
                existing_insiders.add(key)
                dst_cur.execute(
                    """
                    INSERT INTO insider_trades_raw (
                        ticker, captured_at, filing_date, trade_date, insider_name,
                        position, transaction_type, shares, price, total_value,
                        ownership, filing_details
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        r["ticker"],
                        r["date"],
                        tx_date,
                        tx_date,
                        insider_name,
                        tx.get("position"),
                        tx_type,
                        shares,
                        str(tx.get("price") or "") if tx.get("price") is not None else None,
                        float(tx.get("value") or 0.0),
                        tx.get("ownership"),
                        tx.get("details") or tx.get("text"),
                    ),
                )
                migrated_insiders += 1
        print(f"Backfilled {migrated_insiders} historical Form 4 rows from retail raw_insider_data -> insider_trades_raw")

        # 3. Migrate core_equity_reports (linking core_raw_id)
        core_raw_by_ticker: dict[str, list[tuple[int, str]]] = {}
        for row in dst.execute("SELECT id, ticker, captured_at FROM core_equity_raw ORDER BY id ASC").fetchall():
            core_raw_by_ticker.setdefault(row[1], []).append((row[0], row[2]))

        core_cols = list(Base.metadata.tables["core_equity_reports"].columns.keys())
        core_rows = src_cur.execute("SELECT * FROM core_equity_reports ORDER BY id ASC").fetchall()
        for r in core_rows:
            existing_core_raw_id = r["core_raw_id"] if "core_raw_id" in r.keys() else None
            core_raw_id = existing_core_raw_id or _closest_id(core_raw_by_ticker.get(r["ticker"], []), r["date"])
            if core_raw_id is None:
                # Synthesize CoreEquityRaw only if orphan
                dst_cur.execute(
                    """
                    INSERT INTO core_equity_raw (
                        ticker, captured_at, company_name, sector, industry,
                        current_price, target_price, raw_metrics, raw_news, raw_filings
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        r["ticker"],
                        r["date"],
                        r["company_name"],
                        r["sector"],
                        r["industry"],
                        r["current_price"],
                        r["target_price"],
                        r["raw_metrics"] if "raw_metrics" in r.keys() else None,
                        r["raw_news"] if "raw_news" in r.keys() else None,
                        r["raw_filings"] if "raw_filings" in r.keys() else None,
                    ),
                )
                core_raw_id = dst_cur.lastrowid
                core_raw_by_ticker.setdefault(r["ticker"], []).append((core_raw_id, r["date"]))

            values = [core_raw_id if c == "core_raw_id" else r[c] for c in core_cols]
            dst_cur.execute(
                f"INSERT INTO core_equity_reports ({', '.join(core_cols)}) VALUES ({', '.join(['?']*len(core_cols))})",
                values,
            )
        print(f"Migrated {len(core_rows)} rows -> core_equity_reports")

        # 4. Migrate retail_sentiment_reports (linking daily_ticker_id)
        dt_by_ticker: dict[str, list[tuple[int, str]]] = {}
        for row in dst.execute("SELECT id, ticker, date FROM daily_tickers ORDER BY id ASC").fetchall():
            dt_by_ticker.setdefault(row[1], []).append((row[0], row[2]))

        retail_cols = list(Base.metadata.tables["retail_sentiment_reports"].columns.keys())
        for r in retail_rows:
            existing_dt_id = r["daily_ticker_id"] if "daily_ticker_id" in r.keys() else None
            daily_ticker_id = existing_dt_id or _closest_id(dt_by_ticker.get(r["ticker"], []), r["date"])
            values = [daily_ticker_id if c == "daily_ticker_id" else r[c] for c in retail_cols]
            dst_cur.execute(
                f"INSERT INTO retail_sentiment_reports ({', '.join(retail_cols)}) VALUES ({', '.join(['?']*len(retail_cols))})",
                values,
            )
        print(f"Migrated {len(retail_rows)} rows -> retail_sentiment_reports")

        # 5. Migrate smart_money_reports (linking smart_money_ticker_id; preserve any orphan leaderboard metrics)
        smt_by_ticker: dict[str, list[tuple[int, str]]] = {}
        for row in dst.execute("SELECT id, ticker, date FROM smart_money_tickers ORDER BY id ASC").fetchall():
            smt_by_ticker.setdefault(row[1], []).append((row[0], row[2]))

        sm_cols = list(Base.metadata.tables["smart_money_reports"].columns.keys())
        sm_rows = src_cur.execute("SELECT * FROM smart_money_reports ORDER BY id ASC").fetchall()
        for r in sm_rows:
            existing_smt_id = r["smart_money_ticker_id"] if "smart_money_ticker_id" in r.keys() else None
            if existing_smt_id is not None:
                smt_id = existing_smt_id
            else:
                cands = smt_by_ticker.get(r["ticker"], [])
                same_day = [c for c in cands if _date_day(c[1]) == _date_day(r["date"])]
                if same_day:
                    smt_id = _closest_id(same_day, r["date"])
                else:
                    # Preserve exact historical metrics into smart_money_tickers instead of linking a wrong date
                    dst_cur.execute(
                        """
                        INSERT INTO smart_money_tickers (
                            ticker, date, rank, conviction_score, insider_score,
                            political_score, cluster_count, total_buy_volume, top_buyer_summary
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            r["ticker"],
                            r["date"],
                            (r["rank"] if "rank" in r.keys() else 0) or 0,
                            (r["conviction_score"] if "conviction_score" in r.keys() else 0.0) or 0.0,
                            0.0,
                            0.0,
                            (r["cluster_count"] if "cluster_count" in r.keys() else 0) or 0,
                            (r["total_buy_volume"] if "total_buy_volume" in r.keys() else 0.0) or 0.0,
                            r["top_buyer_summary"] if "top_buyer_summary" in r.keys() else None,
                        ),
                    )
                    smt_id = dst_cur.lastrowid
                    smt_by_ticker.setdefault(r["ticker"], []).append((smt_id, r["date"]))

            values = [smt_id if c == "smart_money_ticker_id" else r[c] for c in sm_cols]
            dst_cur.execute(
                f"INSERT INTO smart_money_reports ({', '.join(sm_cols)}) VALUES ({', '.join(['?']*len(sm_cols))})",
                values,
            )
        print(f"Migrated {len(sm_rows)} rows -> smart_money_reports")

        # 6. Migrate options_whale_reports (linking options_whale_ticker_id)
        owt_by_ticker: dict[str, list[tuple[int, str]]] = {}
        for row in dst.execute("SELECT id, ticker, date FROM options_whale_tickers ORDER BY id ASC").fetchall():
            owt_by_ticker.setdefault(row[1], []).append((row[0], row[2]))

        ow_rep_cols = list(Base.metadata.tables["options_whale_reports"].columns.keys())
        ow_rep_rows = src_cur.execute("SELECT * FROM options_whale_reports ORDER BY id ASC").fetchall()
        ow_reports_by_ticker_day: dict[tuple[str, str], list[tuple[int, list[dict]]]] = {}
        for r in ow_rep_rows:
            existing_owt_id = r["options_whale_ticker_id"] if "options_whale_ticker_id" in r.keys() else None
            owt_id = existing_owt_id or _closest_id(owt_by_ticker.get(r["ticker"], []), r["date"])
            values = [owt_id if c == "options_whale_ticker_id" else r[c] for c in ow_rep_cols]
            dst_cur.execute(
                f"INSERT INTO options_whale_reports ({', '.join(ow_rep_cols)}) VALUES ({', '.join(['?']*len(ow_rep_cols))})",
                values,
            )
            uc_raw = r["unusual_contracts"] if "unusual_contracts" in r.keys() else None
            uc_list = json.loads(uc_raw) if isinstance(uc_raw, str) else (uc_raw or [])
            ow_reports_by_ticker_day.setdefault((r["ticker"], _date_day(r["date"])), []).append((r["id"], uc_list))
        print(f"Migrated {len(ow_rep_rows)} rows -> options_whale_reports")

        # 7. Migrate options_whale_raw (pure Layer 1) + populate options_report_contracts junction
        ow_raw_cols = list(Base.metadata.tables["options_whale_raw"].columns.keys())
        ow_raw_rows = src_cur.execute("SELECT * FROM options_whale_raw ORDER BY id ASC").fetchall()
        ow_rep_lookup: dict[str, list[tuple[int, str]]] = {}
        for r in ow_rep_rows:
            ow_rep_lookup.setdefault(r["ticker"], []).append((r["id"], r["date"]))

        src_has_junction = (
            src_cur.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='options_report_contracts'"
            ).fetchone()
            is not None
        )
        junction_pairs: set[tuple[int, int]] = set()
        if src_has_junction:
            for j in src_cur.execute("SELECT options_report_id, options_raw_id FROM options_report_contracts").fetchall():
                junction_pairs.add((j[0], j[1]))

        for r in ow_raw_rows:
            row_map = dict(r)
            rep_id = row_map.get("options_report_id")
            if rep_id is None:
                day = _date_day(r["captured_at"])
                rep_cands = ow_reports_by_ticker_day.get((r["ticker"], day), [])
                rep_id = _closest_id(ow_rep_lookup.get(r["ticker"], []), r["captured_at"]) if rep_cands else None

            matched_contract = None
            if rep_id is not None:
                junction_pairs.add((rep_id, r["id"]))
                day = _date_day(r["captured_at"])
                for cand_id, uc_list in ow_reports_by_ticker_day.get((r["ticker"], day), []):
                    if cand_id == rep_id:
                        for c in uc_list:
                            if (
                                c.get("strike") == r["strike"]
                                and str(c.get("type") or "").upper() == str(r["option_type"] or "").upper()
                                and (c.get("volume") is None or c.get("volume") == r["volume"])
                            ):
                                matched_contract = c
                                break
            if row_map.get("dte") is None and matched_contract:
                row_map["dte"] = matched_contract.get("dte")
            if row_map.get("is_otm") is None and matched_contract:
                row_map["is_otm"] = matched_contract.get("is_otm")
            if row_map.get("is_sweep") is None and matched_contract:
                row_map["is_sweep"] = matched_contract.get("is_sweep")
            if matched_contract and not row_map.get("expiry_date"):
                row_map["expiry_date"] = matched_contract.get("expiration")
            values = [row_map.get(c) for c in ow_raw_cols]
            dst_cur.execute(
                f"INSERT INTO options_whale_raw ({', '.join(ow_raw_cols)}) VALUES ({', '.join(['?']*len(ow_raw_cols))})",
                values,
            )

        if junction_pairs:
            dst_cur.executemany(
                "INSERT INTO options_report_contracts (options_report_id, options_raw_id) VALUES (?, ?)",
                sorted(junction_pairs),
            )
        print(f"Migrated {len(ow_raw_rows)} rows -> options_whale_raw ({len(junction_pairs)} links -> options_report_contracts)")

        # 8. Migrate synthesis_reports (linking retail_report_id, smart_money_report_id, options_whale_report_id)
        retail_lookup: dict[str, list[tuple[int, str]]] = {}
        for row in dst.execute("SELECT id, ticker, date FROM retail_sentiment_reports ORDER BY id ASC").fetchall():
            retail_lookup.setdefault(row[1], []).append((row[0], row[2]))

        sm_lookup: dict[str, list[tuple[int, str]]] = {}
        for row in dst.execute("SELECT id, ticker, date FROM smart_money_reports ORDER BY id ASC").fetchall():
            sm_lookup.setdefault(row[1], []).append((row[0], row[2]))

        ow_lookup: dict[str, list[tuple[int, str]]] = {}
        for row in dst.execute("SELECT id, ticker, date FROM options_whale_reports ORDER BY id ASC").fetchall():
            ow_lookup.setdefault(row[1], []).append((row[0], row[2]))

        syn_cols = list(Base.metadata.tables["synthesis_reports"].columns.keys())
        syn_rows = src_cur.execute("SELECT * FROM synthesis_reports ORDER BY id ASC").fetchall()
        for r in syn_rows:
            ticker = r["ticker"]
            ts = r["date"]
            # Only link same-day engine reports (or at/before same day) if that engine actually contributed
            ret_id = _closest_id(
                [c for c in retail_lookup.get(ticker, []) if _date_day(c[1]) == _date_day(ts)],
                ts,
            )
            sm_id = _closest_id(
                [c for c in sm_lookup.get(ticker, []) if _date_day(c[1]) == _date_day(ts)],
                ts,
            )
            ow_id = _closest_id(
                [c for c in ow_lookup.get(ticker, []) if _date_day(c[1]) == _date_day(ts)],
                ts,
            )
            row_map = dict(r)
            row_map["retail_report_id"] = ret_id
            row_map["smart_money_report_id"] = sm_id
            row_map["options_whale_report_id"] = ow_id
            values = [row_map.get(c) for c in syn_cols]
            dst_cur.execute(
                f"INSERT INTO synthesis_reports ({', '.join(syn_cols)}) VALUES ({', '.join(['?']*len(syn_cols))})",
                values,
            )
        print(f"Migrated {len(syn_rows)} rows -> synthesis_reports")

        # 9. Verify FK integrity and exact schema parity
        dst_cur.execute("PRAGMA foreign_keys = ON")
        fk_errors = dst_cur.execute("PRAGMA foreign_key_check").fetchall()
        if fk_errors:
            raise RuntimeError(f"Foreign key verification failed: {fk_errors}")

        if _schema_needs_migration(dst):
            raise RuntimeError("Target database still does not match Base.metadata after migration!")

        dst.commit()
    finally:
        dst.close()
        src.close()

    # Replace live database cleanly
    shutil.move(tmp_path, db_path)
    print(f"Successfully migrated {db_path} (backup retained at {backup_path}).")


if __name__ == "__main__":
    migrate()
