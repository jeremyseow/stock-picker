import os
import sys
import asyncio
import logging
import subprocess
from pathlib import Path

# 1. Resolve backend directory
backend_dir = Path(__file__).resolve().parent

# 2. Virtual Environment Auto-Detection
# If running with a global/system Python instead of the backend venv, seamlessly re-exec
venv_python = backend_dir / ".venv" / "Scripts" / "python.exe"
if venv_python.exists() and Path(sys.executable).resolve() != venv_python.resolve():
    print(f"[run_pipeline] Launching in project virtual environment: {venv_python}", flush=True)
    res = subprocess.run([str(venv_python), *sys.argv], cwd=str(backend_dir))
    sys.exit(res.returncode)

# 3. Ensure stdout & stderr are line-buffered
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(line_buffering=True)

# 4. Configure logging BEFORE importing application modules (with force=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    force=True,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("run_pipeline")

# 5. Ensure backend root is on sys.path and load environment variables
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
load_dotenv(backend_dir / ".env")

# 6. Import engine pipelines
from app.pipeline import run_analysis_pipeline
from app.smart_money_pipeline import run_smart_money_pipeline
from app.options_pipeline import run_options_pipeline
from app.synthesis_engine import generate_cross_engine_synthesis
from app.database import AsyncSessionLocal


async def main():
    print("\n" + "=" * 65, flush=True)
    print("🚀 Antigravity StockPicker: Starting Full Multi-Engine Pipeline", flush=True)
    print("=" * 65 + "\n", flush=True)

    try:
        logger.info("=== [Step 1/4: Engine 1 (Retail Momentum)] Starting... ===")
        await run_analysis_pipeline()

        logger.info("=== [Step 2/4: Engine 2 (Smart Money Scout)] Starting... ===")
        await run_smart_money_pipeline(limit=5)

        logger.info("=== [Step 3/4: Engine 3 (Whale Options Radar)] Starting... ===")
        await run_options_pipeline(limit=5)

        logger.info("=== [Step 4/4: Triangulation Synthesis Matrix] Correlating signals... ===")
        async with AsyncSessionLocal() as db:
            await generate_cross_engine_synthesis(db)

        print("\n" + "=" * 65, flush=True)
        print("✅ All 3 engines and Triangulation Synthesis completed successfully!", flush=True)
        print("=" * 65 + "\n", flush=True)

    except Exception as e:
        logger.exception(f"❌ Error during pipeline execution: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
