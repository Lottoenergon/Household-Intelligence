"""
run_pipeline.py
Master Orchestrator for Pillar 2: Jabodetabek Rental Housing & Market Intelligence.
Runs Ingestion -> Transformation -> Market Intelligence (Valuation) -> DB Sync.
"""

import os
import sys
import subprocess
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(base_dir, "src")
    
    logger.info("=" * 75)
    logger.info("STARTING JABODETABEK RENTAL HOUSING MARKET INTELLIGENCE PIPELINE")
    logger.info("=" * 75)

    # 1. Ingestion (Optional flag --skip-ingest to use existing raw json)
    raw_json = os.path.join(base_dir, "data", "raw", "raw_rental_listings_staged.json")
    if "--fresh-crawl" in sys.argv or not os.path.exists(raw_json):
        logger.info("\n[Phase 1/3] Ingestion: Extracting live listings from property portal...")
        subprocess.run([sys.executable, os.path.join(src_dir, "ingestion.py")], check=True)
    else:
        logger.info(f"\n[Phase 1/3] Ingestion: Using existing raw staged dataset ({raw_json}).")

    # 2. Transformation
    logger.info("\n[Phase 2/3] Transformation: Normalizing prices, features & locations...")
    subprocess.run([sys.executable, os.path.join(src_dir, "transformation.py")], check=True)

    # 3. Market Intelligence & SQL Sync
    logger.info("\n[Phase 3/3] Market Intelligence: Hedonic Valuation & Database Sync...")
    subprocess.run([sys.executable, os.path.join(src_dir, "market_intelligence.py")], check=True)

    logger.info("\n" + "=" * 75)
    logger.info("PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
    logger.info(" -> Processed CSV: data/processed/jabodetabek_rental_evaluated.csv")
    logger.info(" -> SQLite DB:     data/processed/rental_intelligence.db")
    logger.info(" -> Run Dashboard: streamlit run app.py")
    logger.info("=" * 75)


if __name__ == "__main__":
    main()
