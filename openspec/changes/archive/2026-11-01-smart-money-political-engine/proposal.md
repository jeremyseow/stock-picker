## Why

Currently, all market discovery is driven by social media volume (Reddit), which tends to be reactive, noisy, and late-stage. By introducing a parallel "Smart Money & Political Scout" (Engine 2) that originates directly from SEC Form 4 insider cluster buys and Congressional STOCK Act disclosures, the system can discover medium-term swing opportunities before catalysts are realized and before retail becomes aware. Running both engines independently and synthesizing their intersection provides a comprehensive perspective on market sentiment versus insider positioning.

## What Changes

- **Engine 2 Data Ingestion**: Automated ingestion of daily SEC Form 4 open-market cash purchases (Code P) and Congressional STOCK Act Periodic Transaction Reports (House and Senate PTRs).
- **Conviction Scoring & Noise Filtering**: Multi-factor conviction formula prioritizing C-suite leadership (3x), Congressional committee jurisdiction matches (3x), cluster buying intensity (2.5x), and significant position growth, while filtering out non-cash grants, routine options, and stale trades.
- **Macro & Political Research Deep-Dive**: Targeted LLM research agent connecting identified stocks to pending congressional legislation, defense contract awards, FDA calendar milestones, and regulatory shifts.
- **Cross-Engine Synthesis Hub**: Correlation engine classifying ticker overlaps into four core archetypes: The Rocket (Full Alignment), The Retail Trap (Bearish Divergence), Silent Accumulation (Pre-Catalyst Stealth Entry), and Market Noise.
- **Distinct Reporting Surfaces**: Keep the Engine 1 Retail Momentum dashboard intact while introducing dedicated reporting surfaces for Engine 2 (`/smart-money`) and the Cross-Engine Synthesis Matrix (`/synthesis`).

## Capabilities

### New Capabilities
- `smart-money-scout`: Ingests, filters, and scores corporate insider cluster buys and Congressional STOCK Act disclosures across the market, conducting macroeconomic and legislative research on top candidates.
- `cross-engine-synthesis`: Reconciles retail momentum from Engine 1 with smart money positioning from Engine 2 to produce archetype diagnoses, awareness metrics, and swing trade theses.

### Modified Capabilities
- `dashboard-frontend`: Introduces dedicated navigation tabs and separate report views for Smart Money (`/smart-money`, `/smart-money/[ticker]`) and the Cross-Engine Synthesis Matrix (`/synthesis`), preserving the existing Retail Momentum dashboard (`/`, `/report/[ticker]`) unchanged.

## Impact

- **Backend**:
  - New ingestion worker module: `backend/app/smart_money_ingestor.py` (SEC Form 4 and Congressional PTR streams).
  - New scoring & filtering module: `backend/app/smart_money_scorer.py`.
  - New synthesis engine: `backend/app/synthesis_engine.py`.
  - Database schema additions in `backend/app/models.py` to persist Engine 2 candidate picks, Smart Money reports, and cross-engine synthesis records.
  - New FastAPI endpoints in `backend/app/main.py` serving Smart Money reports and synthesis matrices.
- **Frontend**:
  - Top navigation bar updated with "Retail Momentum", "Smart Money & Gov", and "Synthesis Matrix" tabs.
  - New route pages: `/smart-money`, `/smart-money/[ticker]`, and `/synthesis`.
- **Pipeline & Scheduler**:
  - Engine 2 runner integrated into `backend/app/pipeline.py` or scheduled independently post-market.

