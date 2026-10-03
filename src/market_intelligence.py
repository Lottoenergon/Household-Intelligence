"""
market_intelligence.py
Production Econometric Hedonic Pricing Valuation & Deal Finder Engine.
Builds an econometrics and machine learning valuation model to estimate fair market rent,
identifies statistically undervalued rental listings, and populates the Star Schema SQLite DB.
"""

import os
import sys
import json
import sqlite3
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from sklearn.model_selection import KFold, cross_val_score
from sklearn.linear_model import Ridge
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def build_hedonic_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, list]:
    """Prepares feature matrix for Hedonic Pricing Model."""
    feature_df = pd.DataFrame(index=df.index)
    
    # 1. Structural features (log-transformed size for diminishing returns)
    feature_df["log_floor_size"] = np.log(df["floor_size_m2"])
    feature_df["bedrooms"] = df["bedrooms"]
    feature_df["bathrooms"] = df["bathrooms"]

    # 2. Geospatial distance features
    feature_df["distance_to_cbd_km"] = df["distance_to_cbd_km"]
    feature_df["distance_to_transit_km"] = df["distance_to_transit_km"]

    # 3. Amenity and furnishing vectors
    amenity_cols = [
        "is_full_furnished", "is_semi_furnished", "has_ac", "has_wifi",
        "has_water_heater", "has_pool", "has_gym", "near_transit",
        "has_balcony", "has_kitchen", "has_parking"
    ]
    for col in amenity_cols:
        feature_df[col] = df[col].astype(int)

    # 4. Location fixed effects (One-Hot Encoded City dummy variables)
    city_dummies = pd.get_dummies(df["target_city"], prefix="city", drop_first=True)
    for col in city_dummies.columns:
        feature_df[col] = city_dummies[col].astype(int)

    # Target variable: Log-transformed monthly rent (stabilizes variance & skewness)
    y_log = np.log(df["price_monthly_idr"])

    return feature_df, y_log, list(feature_df.columns)


def train_and_evaluate_models(X: pd.DataFrame, y_log: pd.Series, y_actual: pd.Series) -> Tuple[Any, Dict[str, Any]]:
    """Trains Ridge and Gradient Boosting models, evaluates with 5-fold CV."""
    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    # Model 1: Econometric Ridge Regression
    ridge_model = Ridge(alpha=1.0)
    ridge_r2_scores = cross_val_score(ridge_model, X, y_log, cv=kf, scoring="r2")

    # Model 2: Non-linear Gradient Boosting Regressor
    gb_model = GradientBoostingRegressor(
        n_estimators=180,
        learning_rate=0.06,
        max_depth=4,
        subsample=0.85,
        random_state=42
    )
    gb_r2_scores = cross_val_score(gb_model, X, y_log, cv=kf, scoring="r2")

    # Fit final GB model on full dataset
    gb_model.fit(X, y_log)
    pred_log = gb_model.predict(X)
    pred_actual = np.exp(pred_log)

    r2_full = float(r2_score(y_actual, pred_actual))
    mae = float(mean_absolute_error(y_actual, pred_actual))
    rmse = float(np.sqrt(mean_squared_error(y_actual, pred_actual)))
    mape = float(np.mean(np.abs((y_actual - pred_actual) / y_actual)) * 100.0)

    # Feature Importance ranking
    importances = gb_model.feature_importances_
    feature_imp = sorted(
        [{"feature": col, "importance": round(float(imp), 4)} for col, imp in zip(X.columns, importances)],
        key=lambda x: x["importance"],
        reverse=True
    )

    metrics = {
        "model_type": "GradientBoostingRegressor (Hedonic Price Engine)",
        "cv_r2_mean_gb": round(float(gb_r2_scores.mean()), 4),
        "cv_r2_mean_ridge": round(float(ridge_r2_scores.mean()), 4),
        "full_dataset_r2": round(r2_full, 4),
        "mae_idr": round(mae, 0),
        "rmse_idr": round(rmse, 0),
        "mape_pct": round(mape, 2),
        "sample_size": len(X),
        "feature_importances": feature_imp[:10]
    }

    logger.info(f"Model Training Results: CV R2 = {metrics['cv_r2_mean_gb']:.3f} | Full R2 = {r2_full:.3f} | MAE = Rp {mae:,.0f} ({mape:.1f}%)")
    return gb_model, metrics


def compute_deal_scores(df: pd.DataFrame, fair_rent: np.ndarray) -> pd.DataFrame:
    """Computes standardized residual and deal classification for each property."""
    df_eval = df.copy()
    df_eval["fair_market_rent_idr"] = np.round(fair_rent, 0)
    df_eval["residual_idr"] = df_eval["price_monthly_idr"] - df_eval["fair_market_rent_idr"]
    df_eval["discount_pct"] = np.round((df_eval["fair_market_rent_idr"] - df_eval["price_monthly_idr"]) / df_eval["fair_market_rent_idr"] * 100.0, 1)

    # Standardized residual Z-score (Z = residual / std_err)
    residual_std = df_eval["residual_idr"].std()
    df_eval["deal_score_z"] = np.round(df_eval["residual_idr"] / residual_std, 2)

    def classify_deal(z: float) -> str:
        if z <= -1.5:
            return "Deep Value Deal (Rare Find)"
        elif z <= -0.75:
            return "Good Deal (Undervalued)"
        elif z < 0.75:
            return "Fair Market Price"
        elif z < 1.5:
            return "Premium / High Price"
        else:
            return "Overpriced / Luxury Tag"

    df_eval["deal_classification"] = df_eval["deal_score_z"].apply(classify_deal)
    return df_eval


def sync_to_sqlite(df_eval: pd.DataFrame, schema_sql_path: str, db_path: str):
    """Populates Star Schema tables and compiles analytical SQL views in SQLite."""
    logger.info(f"Populating Star Schema database at {db_path}...")
    
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 1. Execute DDL and schema creation
    with open(schema_sql_path, "r", encoding="utf-8") as f:
        schema_script = f.read()
    cur.executescript(schema_script)
    conn.commit()

    # 2. Insert Dimension: Locations
    loc_cols = [
        "subdistrict", "target_city", "target_province", "urban_zone",
        "latitude", "longitude", "distance_to_cbd_km", "nearest_transit_hub", "distance_to_transit_km"
    ]
    df_locations = df_eval[loc_cols].drop_duplicates().reset_index(drop=True)
    df_locations.index += 1
    df_locations.reset_index(names=["location_key"], inplace=True)
    df_locations.to_sql("dim_locations", conn, if_exists="append", index=False)

    # 3. Insert Dimension: Property Specs
    spec_cols = ["property_type", "bedrooms", "bathrooms", "layout_category", "floor_size_m2"]
    df_specs = df_eval[spec_cols].drop_duplicates().reset_index(drop=True)
    df_specs.index += 1
    df_specs.reset_index(names=["spec_key"], inplace=True)
    df_specs.to_sql("dim_property_specs", conn, if_exists="append", index=False)

    # 4. Insert Dimension: Amenities
    amenity_cols = [
        "is_full_furnished", "is_semi_furnished", "is_unfurnished", "has_ac", "has_wifi",
        "has_water_heater", "has_pool", "has_gym", "has_balcony", "has_kitchen", "near_transit", "has_parking"
    ]
    df_amenities = df_eval[amenity_cols].drop_duplicates().reset_index(drop=True)
    df_amenities.index += 1
    df_amenities.reset_index(names=["amenity_key"], inplace=True)
    df_amenities.to_sql("dim_amenities", conn, if_exists="append", index=False)

    # 5. Map surrogate keys back to Fact Table
    df_fact = df_eval.merge(df_locations, on=loc_cols, how="left")
    df_fact = df_fact.merge(df_specs, on=spec_cols, how="left")
    df_fact = df_fact.merge(df_amenities, on=amenity_cols, how="left")

    fact_cols = [
        "listing_id", "location_key", "spec_key", "amenity_key",
        "title", "url", "price_monthly_idr", "price_per_m2_idr", "original_period",
        "fair_market_rent_idr", "residual_idr", "discount_pct", "deal_score_z",
        "deal_classification", "image_url", "short_description"
    ]
    df_fact_table = df_fact[fact_cols].copy()
    df_fact_table.to_sql("fact_rental_listings", conn, if_exists="append", index=False)
    conn.commit()

    # 6. Verify analytical views
    views_to_test = [
        "view_city_market_benchmarks",
        "view_urban_zone_distance_decay",
        "view_transit_proximity_premium",
        "view_layout_and_bedroom_matrix",
        "view_top_undervalued_deals",
        "view_amenity_hedonic_premiums"
    ]
    for v in views_to_test:
        count = cur.execute(f"SELECT COUNT(*) FROM {v}").fetchone()[0]
        logger.info(f"Verified SQL View: {v} -> {count} rows")

    conn.close()
    logger.info("Star Schema and all 6 Analytical Views successfully compiled in SQLite!")


def run_market_intelligence_pipeline(base_dir: str = "."):
    proc_dir = os.path.join(base_dir, "data", "processed")
    sql_path = os.path.join(base_dir, "sql", "schema.sql")
    clean_csv_path = os.path.join(proc_dir, "jabodetabek_rental_cleaned.csv")
    eval_csv_path = os.path.join(proc_dir, "jabodetabek_rental_evaluated.csv")
    metrics_json_path = os.path.join(proc_dir, "model_evaluation_metrics.json")
    db_path = os.path.join(proc_dir, "rental_intelligence.db")

    logger.info(f"Loading cleaned dataset from {clean_csv_path}...")
    df = pd.read_csv(clean_csv_path)

    # 1. Feature matrix & Target
    X, y_log, feat_names = build_hedonic_features(df)

    # 2. Train Hedonic Pricing Model
    gb_model, metrics = train_and_evaluate_models(X, y_log, df["price_monthly_idr"])

    # 3. Predict Fair Market Rent & Deal Score
    fair_rent = np.exp(gb_model.predict(X))
    df_evaluated = compute_deal_scores(df, fair_rent)

    # 4. Save evaluated dataset and metrics
    df_evaluated.to_csv(eval_csv_path, index=False, encoding="utf-8")
    with open(metrics_json_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    # 5. Sync to Relational Star Schema DB
    sync_to_sqlite(df_evaluated, sql_path, db_path)

    # 6. Log Top 5 Undervalued Bargains
    top_deals = df_evaluated.sort_values("deal_score_z").head(5)
    logger.info("=== TOP 5 MOST UNDERVALUED LISTINGS (DEAL HUNTER) ===")
    for _, r in top_deals.iterrows():
        logger.info(
            f"[{r['target_city']}] {r['title']} | Actual: Rp {r['price_monthly_idr']:,.0f} | "
            f"Fair Market: Rp {r['fair_market_rent_idr']:,.0f} | Discount: {r['discount_pct']:.1f}% (Z = {r['deal_score_z']:.2f})"
        )


if __name__ == "__main__":
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    run_market_intelligence_pipeline(base)