"""
market_intelligence.py
Hedonic Pricing Valuation & Deal Finder Engine.
Builds an econometrics/ML baseline to evaluate fair rental market price
and identifies undervalued 'Good Deal' apartment listings across Jabodetabek.
"""

import os
import sys
import json
import logging
import sqlite3
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, r2_score

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def build_valuation_model(df: pd.DataFrame):
    """
    Fits a robust Gradient Boosting Hedonic Pricing model on log-transformed monthly rent.
    Features: City, Bedrooms, Bathrooms, Floor Size, Furnishing, Amenities.
    """
    feature_cols = [
        "target_city", "bedrooms", "bathrooms", "floor_size_m2",
        "is_full_furnished", "is_semi_furnished", "is_unfurnished",
        "has_ac", "has_wifi", "has_pool", "near_transit", "has_balcony"
    ]
    
    X = df[feature_cols].copy()
    # Log-transform target to handle right-skewed property prices
    y = np.log1p(df["price_monthly_idr"])

    cat_cols = ["target_city"]
    num_cols = [c for c in feature_cols if c not in cat_cols]

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(drop="first", sparse_output=False), cat_cols),
            ("num", "passthrough", num_cols)
        ]
    )

    model = Pipeline([
        ("preprocessor", preprocessor),
        ("regressor", GradientBoostingRegressor(
            n_estimators=120,
            learning_rate=0.08,
            max_depth=4,
            random_state=42
        ))
    ])

    model.fit(X, y)
    preds_log = model.predict(X)
    preds_price = np.expm1(preds_log)

    mae = mean_absolute_error(df["price_monthly_idr"], preds_price)
    r2 = r2_score(y, preds_log)
    logger.info(f"Hedonic Pricing Model trained: R2 (log) = {r2:.3f}, MAE = Rp {mae:,.0f}")

    df["estimated_fair_price"] = preds_price
    
    # Valuation Discount % = (Fair Price - Actual Price) / Fair Price * 100
    # Positive discount means property is CHEAPER than market fair value (Undervalued)
    df["undervalued_discount_pct"] = (
        (df["estimated_fair_price"] - df["price_monthly_idr"]) / df["estimated_fair_price"] * 100
    )

    def classify_deal(discount):
        if discount >= 25.0:
            return "High Value Deal (>25% Discount)"
        elif discount >= 10.0:
            return "Fair Value Deal (10-25% Discount)"
        elif discount <= -25.0:
            return "Overpriced (>25% Premium)"
        elif discount <= -10.0:
            return "Above Market (10-25% Premium)"
        else:
            return "Market Standard"

    df["valuation_status"] = df["undervalued_discount_pct"].apply(classify_deal)
    return df, model


def sync_to_database(df: pd.DataFrame, db_path: str, sql_schema_path: str):
    logger.info(f"Syncing analytical tables to SQLite database at {db_path}...")
    conn = sqlite3.connect(db_path)
    
    # Execute DDL
    with open(sql_schema_path, "r", encoding="utf-8") as f:
        conn.executescript(f.read())

    # Ingest fact table
    fact_cols = [
        "listing_id", "title", "url", "target_city", "subdistrict", "target_province",
        "price_monthly_idr", "price_per_m2_idr", "original_period",
        "bedrooms", "bathrooms", "floor_size_m2",
        "is_full_furnished", "is_semi_furnished", "is_unfurnished",
        "has_ac", "has_wifi", "has_water_heater", "has_pool", "near_transit", "has_balcony",
        "latitude", "longitude", "estimated_fair_price", "undervalued_discount_pct", "valuation_status"
    ]
    df_db = df[fact_cols].copy()
    df_db.rename(columns={"target_city": "city_name", "target_province": "province"}, inplace=True)
    
    df_db.to_sql("fact_rental_listings", conn, if_exists="append", index=False)
    conn.commit()

    # Smoke test views
    views = [
        "view_city_rental_benchmarks",
        "view_bedroom_rental_pricing",
        "view_top_undervalued_deals",
        "view_amenity_rental_premium"
    ]
    for v in views:
        cnt = conn.execute(f"SELECT COUNT(*) FROM {v}").fetchone()[0]
        logger.info(f"SQL View verified: {v} -> {cnt} rows")

    conn.close()
    logger.info("Database ingestion & view verification complete!")


def run_market_intelligence():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    clean_csv_path = os.path.join(base_dir, "data", "processed", "jabodetabek_rental_cleaned.csv")
    db_path = os.path.join(base_dir, "data", "processed", "rental_intelligence.db")
    sql_path = os.path.join(base_dir, "sql", "schema.sql")

    logger.info(f"Loading cleaned dataset from {clean_csv_path}...")
    df = pd.read_csv(clean_csv_path)

    df_evaluated, model = build_valuation_model(df)

    # Save evaluated dataframe
    evaluated_csv_path = os.path.join(base_dir, "data", "processed", "jabodetabek_rental_evaluated.csv")
    df_evaluated.to_csv(evaluated_csv_path, index=False, encoding="utf-8")
    logger.info(f"Evaluated records saved to {evaluated_csv_path}")

    # Sync to SQLite
    sync_to_database(df_evaluated, db_path, sql_path)

    # Print Summary Insights
    logger.info("\n=== TOP 5 MOST UNDERVALUED LISTINGS (DEAL HUNTER) ===")
    top_deals = df_evaluated[df_evaluated["valuation_status"].str.contains("Deal")].sort_values(
        "undervalued_discount_pct", ascending=False
    ).head(5)
    for _, row in top_deals.iterrows():
        logger.info(
            f"[{row['target_city']}] {row['title']} | Actual: Rp {row['price_monthly_idr']:,.0f} | "
            f"Fair Market: Rp {row['estimated_fair_price']:,.0f} | Discount: {row['undervalued_discount_pct']:.1f}%"
        )


if __name__ == "__main__":
    run_market_intelligence()
