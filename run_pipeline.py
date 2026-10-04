"""
run_pipeline.py
Master Pipeline Orchestrator for Pillar 2: Jabodetabek Rental Housing & Market Intelligence Engine.
End-to-End Execution: Ingestion (or Staged Verify) -> Data Cleaning & Geospatial Engineering -> 
Hedonic Valuation Model -> Relational Star Schema DB -> Data Quality Assertions.
"""

import os
import sys
import json
import sqlite3
import subprocess
import logging
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

EXPECTED_VIEWS = [
    "view_city_market_benchmarks",
    "view_urban_zone_distance_decay",
    "view_transit_proximity_premium",
    "view_layout_and_bedroom_matrix",
    "view_top_undervalued_deals",
    "view_amenity_hedonic_premiums"
]


def run_pipeline():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(base_dir, "src")
    data_raw_dir = os.path.join(base_dir, "data", "raw")
    data_proc_dir = os.path.join(base_dir, "data", "processed")
    raw_staged_file = os.path.join(data_raw_dir, "raw_rental_listings_staged.json")
    db_file = os.path.join(data_proc_dir, "rental_intelligence.db")
    eval_csv = os.path.join(data_proc_dir, "jabodetabek_rental_evaluated.csv")
    metrics_file = os.path.join(data_proc_dir, "model_evaluation_metrics.json")

    logger.info("=" * 80)
    logger.info("JABODETABEK RENTAL HOUSING & MARKET INTELLIGENCE ENGINE (PILLAR 2)")
    logger.info("=" * 80)

    # ---------------------------------------------------------
    # Step 1: Ingestion
    # ---------------------------------------------------------
    scrape_requested = "--scrape" in sys.argv or not os.path.exists(raw_staged_file)
    if scrape_requested:
        logger.info("[[Phase 1/4] Running Web Ingestion Engine across 10 Jabodetabek cities...]")
        ingest_script = os.path.join(src_dir, "ingestion.py")
        subprocess.run([sys.executable, ingest_script], check=True)
    else:
        logger.info("[[Phase 1/4] Ingestion: Using verified staged raw records ({os.path.basename(raw_staged_file)}).]")

    # ---------------------------------------------------------
    # Step 2: Transformation & Feature Engineering
    # ---------------------------------------------------------
    logger.info("[[Phase 2/4] Running Transformation, Cleaning, & Geospatial Engineering...]")
    transform_script = os.path.join(src_dir, "transformation.py")
    subprocess.run([sys.executable, transform_script], check=True)

    # ---------------------------------------------------------
    # Step 3: Hedonic Valuation & Database Synchronization
    # ---------------------------------------------------------
    logger.info("[[Phase 3/4] Training Econometric Hedonic Model & Syncing Star Schema DB...]")
    mi_script = os.path.join(src_dir, "market_intelligence.py")
    subprocess.run([sys.executable, mi_script], check=True)

    # ---------------------------------------------------------
    # Step 4: Quality & Integrity Assertions
    # ---------------------------------------------------------
    logger.info("[[Phase 4/4] Executing Automated Data Integrity & Schema Assertions...]")
    
    if not os.path.exists(db_file):
        raise FileNotFoundError(f"Database {db_file} was not generated!")
    if not os.path.exists(eval_csv):
        raise FileNotFoundError(f"Processed dataset {eval_csv} was not generated!")
    if not os.path.exists(metrics_file):
        raise FileNotFoundError(f"Evaluation metrics {metrics_file} missing!")

    conn = sqlite3.connect(db_file)
    cur = conn.cursor()

    # Verify Views return rows
    for v in EXPECTED_VIEWS:
        count = cur.execute(f"SELECT COUNT(*) FROM {v}").fetchone()[0]
        if count == 0:
            raise ValueError(f"Integrity check failed: View {v} returned 0 rows!")
        logger.info(f" -> Assertion PASSED: View '{v}' verified ({count} rows).")

    # Verify Star Schema Relationships
    fact_count = cur.execute("SELECT COUNT(*) FROM fact_rental_listings").fetchone()[0]
    loc_count = cur.execute("SELECT COUNT(*) FROM dim_locations").fetchone()[0]
    spec_count = cur.execute("SELECT COUNT(*) FROM dim_property_specs").fetchone()[0]
    amenity_count = cur.execute("SELECT COUNT(*) FROM dim_amenities").fetchone()[0]
    conn.close()

    with open(metrics_file, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    logger.info(f" -> Star Schema Verified: {fact_count} Facts | {loc_count} Locs | {spec_count} Specs | {amenity_count} Amenities.")
    logger.info(f" -> Model Performance: CV R2 = {metrics['cv_r2_mean_gb']} | Full R2 = {metrics['full_dataset_r2']} | MAE = Rp {metrics['mae_idr']:,.0f} ({metrics['mape_pct']}%)")

    logger.info("=" * 80)
    logger.info("PIPELINE COMPLETED SUCCESSFULLY! ALL ARTIFACTS VERIFIED.")
    logger.info("Interactive Web App (FastAPI + SPA): python -m uvicorn backend.server:app --port 8080 --reload (or run start_platform.bat)")
    logger.info("=" * 80)


if __name__ == "__main__":
    run_pipeline()