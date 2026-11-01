## 1. Database Schema & Data Models

- [x] 1.1 Define `SmartMoneyTicker`, `SmartMoneyReport`, and `SynthesisRecord` SQLAlchemy models in `backend/app/models.py`.
- [x] 1.2 Implement CRUD functions in `backend/app/crud.py` for saving and retrieving Smart Money and Synthesis records.

## 2. Ingestion & Scoring Engine (Engine 2)

- [x] 2.1 Implement `backend/app/smart_money_ingestor.py` fetching market-wide SEC Form 4 cash purchases (Code P) and Congressional STOCK Act disclosures.
- [x] 2.2 Implement `backend/app/smart_money_scorer.py` computing role weights, cluster multipliers, committee relevance, and freshness decay penalties.
- [x] 2.3 Implement `backend/app/smart_money_researcher.py` using LLM agent to investigate government contracts, bills, and swing catalyst horizons.
- [x] 2.4 Implement `backend/app/smart_money_pipeline.py` orchestrating end-to-end Engine 2 execution.

## 3. Cross-Engine Synthesis Hub

- [x] 3.1 Implement `backend/app/synthesis_engine.py` cross-correlating Engine 1 and Engine 2 to classify tickers into the 4 archetypes.
- [x] 3.2 Implement retail awareness timing edge calculation.
- [x] 3.3 Expose FastAPI endpoints for Smart Money feeds (`/api/smart-money/*`) and Synthesis Matrix (`/api/synthesis/*`).

## 4. Frontend Views & Navigation

- [x] 4.1 Update Navbar with "Retail Momentum", "Smart Money & Gov", and "Synthesis Matrix" navigation links.
- [x] 4.2 Build `/smart-money` dashboard and `/smart-money/[ticker]` catalyst report page.
- [x] 4.3 Build `/synthesis` matrix page displaying archetype diagnoses and retail awareness gauges.

## 5. Verification & OpenSpec Validation

- [x] 5.1 Add automated test suite for conviction scoring, committee mapping, and archetype classification.
- [x] 5.2 Verify end-to-end functionality and run `openspec validate smart-money-political-engine --strict`.
