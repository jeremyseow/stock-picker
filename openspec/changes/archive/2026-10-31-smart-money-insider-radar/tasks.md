## 1. Backend Ingestion & Data Extraction

- [x] 1.1 Implement `fetch_insider_data(ticker)` in `backend/app/market_researcher.py` using `yfinance` to extract 6-month aggregate purchases/sales and recent Form 4 transactions.
- [x] 1.2 Implement `fetch_congressional_trades(ticker)` in `backend/app/market_researcher.py` using targeted DuckDuckGo search queries.
- [x] 1.3 Update `StockReport` in `backend/app/llm_schemas.py` to include `smart_money_verdict` and `insider_activity_summary`.
- [x] 1.4 Update database model `TickerReport` in `backend/app/models.py` and `backend/app/crud.py` to persist `smart_money_verdict` and `raw_insider_data`.

## 2. LLM Synthesis & Agent Integration

- [x] 2.1 Update the system prompt in `backend/app/agent.py` to reconcile retail sentiment with Form 4 insider transactions, enforcing that heavy insider selling blocks BUY recommendations.
- [x] 2.2 Update `backend/app/pipeline.py` to collect insider data and forward it to `generate_stock_report`.
- [x] 2.3 Update endpoints in `backend/app/main.py` to serialize insider data and smart money verdicts.

## 3. Frontend Smart Money & Insider Radar UI

- [x] 3.1 Create `SmartMoneyRadar` component in `frontend/src/components/SmartMoneyRadar.tsx` with net flow gauge and Form 4 transactions table.
- [x] 3.2 Integrate `SmartMoneyRadar` into the detailed report page (`frontend/src/app/report/[ticker]/page.tsx`).
- [x] 3.3 Add smart money status badges to report preview cards on the dashboard and historical explorer.

## 4. Verification & Documentation

- [x] 4.1 Add automated test cases in `backend/tests/` verifying insider data extraction, schema serialization, and LLM prompt rules.
- [x] 4.2 Verify frontend build with `npm run build` and run regression tests.
- [x] 4.3 Update `README.md` and project documentation to reflect the new Smart Money radar capabilities.

