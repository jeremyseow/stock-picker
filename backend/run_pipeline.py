import asyncio
import logging
from app.pipeline import run_analysis_pipeline

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    asyncio.run(run_analysis_pipeline())
