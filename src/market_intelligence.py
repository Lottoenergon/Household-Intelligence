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
import joblib
from datetime import datetime, timezone
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from sklearn.model_selection import KFold, GroupKFold
from sklearn.linear_model import Ridge
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

# Ambang klasifikasi deal: satu sumber kebenaran (jangan tulis literal di sini).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deal_config
from deal_config import (  # noqa: E402
    DEAL_DEEP_Z,
    DEAL_GOOD_Z,
    PREMIUM_Z,
    classify_deal,
    is_below_estimate,
    is_deep_value,
    tier_of,
)

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


def _make_gb() -> GradientBoostingRegressor:
    return GradientBoostingRegressor(
        n_estimators=180, learning_rate=0.06, max_depth=4, subsample=0.85, random_state=42
    )


def regression_metrics(actual: np.ndarray, pred: np.ndarray) -> Dict[str, float]:
    """Metrik pada skala Rupiah (kecuali r2_log). MAPE ikut dilaporkan bersama median APE
    karena MAPE sensitif terhadap listing murah/outlier."""
    actual, pred = np.asarray(actual, float), np.asarray(pred, float)
    ape = np.abs(actual - pred) / actual
    return {
        "r2": float(r2_score(actual, pred)),
        "r2_log": float(r2_score(np.log(actual), np.log(pred))),
        "mae_idr": float(mean_absolute_error(actual, pred)),
        "rmse_idr": float(np.sqrt(mean_squared_error(actual, pred))),
        "mape_pct": float(ape.mean() * 100.0),
        "median_ape_pct": float(np.median(ape) * 100.0),
    }


def out_of_fold_log_predictions(df: pd.DataFrame, X: pd.DataFrame, y_log: pd.Series,
                                splits_per_repeat: list) -> Dict[str, np.ndarray]:
    """Prediksi log-harga out-of-fold untuk 3 model: baseline naif, Ridge, Gradient Boosting.

    Setiap baris diprediksi oleh model yang TIDAK pernah melihat baris itu saat latihan.
    Mengembalikan array shape (n_repeat, n_baris) per model.
    Baseline naif = median harga/m2 per kota (dihitung dari data latih saja) x luas unit.
    """
    n = len(X)
    out = {m: np.zeros((len(splits_per_repeat), n)) for m in ("naive", "ridge", "gb")}
    for r, splits in enumerate(splits_per_repeat):
        for tr, te in splits:
            tr_df, te_df = df.iloc[tr], df.iloc[te]
            city_ppm2 = tr_df.groupby("target_city")["price_per_m2_idr"].median()
            fallback = tr_df["price_per_m2_idr"].median()
            naive = te_df["target_city"].map(city_ppm2).fillna(fallback) * te_df["floor_size_m2"]
            out["naive"][r, te] = np.log(naive.values)

            ridge = Ridge(alpha=1.0).fit(X.iloc[tr], y_log.iloc[tr])
            out["ridge"][r, te] = ridge.predict(X.iloc[te])

            gb = _make_gb().fit(X.iloc[tr], y_log.iloc[tr])
            out["gb"][r, te] = gb.predict(X.iloc[te])
    return out


def _summarize(actual: np.ndarray, log_preds: Dict[str, np.ndarray]) -> Dict[str, Any]:
    """Rata-rata dan simpangan baku metrik lintas pengulangan CV, per model."""
    summary = {}
    for model, arr in log_preds.items():
        per_repeat = [regression_metrics(actual, np.exp(arr[r])) for r in range(arr.shape[0])]
        keys = per_repeat[0].keys()
        entry = {}
        for k in keys:
            vals = np.array([m[k] for m in per_repeat])
            entry[k] = round(float(vals.mean()), 4)
            entry[k + "_std"] = round(float(vals.std()), 4) if len(vals) > 1 else None
        summary[model] = entry
    return summary


def train_and_evaluate_models(df: pd.DataFrame, X: pd.DataFrame, y_log: pd.Series,
                              n_splits: int = 5, n_repeats: int = 3, seed: int = 42
                              ) -> Tuple[Any, Dict[str, Any], np.ndarray]:  # array OOF (n_repeat, n_baris)
    """Evaluasi jujur dengan dua skema validasi:

    1. kfold_5x3: KFold acak 5-lipat diulang 3x. Menjawab "seberapa akurat untuk listing BARU di
       area yang sudah dikenal model?" (kasus pemakaian nyata).
    2. group_kfold_subdistrict: GroupKFold, grup = subdistrik. Menjawab "seberapa akurat di
       subdistrik yang belum pernah dilihat?" (uji generalisasi spasial, lebih berat).

    Metrik utama = out-of-fold. R2 in-sample dilaporkan hanya sebagai diagnostik overfit.
    Mengembalikan (model final, metrik, array prediksi log OOF per pengulangan).
    """
    actual = np.exp(y_log.values)

    kfold_splits = [list(KFold(n_splits, shuffle=True, random_state=seed + r).split(X)) for r in range(n_repeats)]
    oof_k = out_of_fold_log_predictions(df, X, y_log, kfold_splits)

    group_splits = [list(GroupKFold(n_splits=n_splits).split(X, groups=df["subdistrict"]))]
    oof_g = out_of_fold_log_predictions(df, X, y_log, group_splits)

    # Model final dilatih di seluruh data (untuk interpretasi & prediksi listing baru)
    gb_final = _make_gb().fit(X, y_log)
    train_r2 = float(r2_score(actual, np.exp(gb_final.predict(X))))

    imp = sorted(
        [{"feature": c, "importance": round(float(i), 4)} for c, i in zip(X.columns, gb_final.feature_importances_)],
        key=lambda d: d["importance"], reverse=True,
    )

    metrics = {
        "model_type": "GradientBoostingRegressor (Hedonic Price Engine)",
        "sample_size": int(len(X)),
        "n_subdistricts": int(df["subdistrict"].nunique()),
        "evaluation": {
            "kfold_5x3": _summarize(actual, oof_k),
            "group_kfold_subdistrict": _summarize(actual, oof_g),
        },
        "train_in_sample_r2_DIAGNOSTIC_ONLY": round(train_r2, 4),
        "feature_importances": imp[:10],
    }
    gb = metrics["evaluation"]["kfold_5x3"]["gb"]
    logger.info(
        f"OOF (KFold 5x3): R2={gb['r2']:.3f} | MAE=Rp {gb['mae_idr']:,.0f} | "
        f"MAPE={gb['mape_pct']:.1f}% | median APE={gb['median_ape_pct']:.1f}% | in-sample R2={train_r2:.3f} (diagnostik)"
    )
    return gb_final, metrics, oof_k["gb"]


def compute_deal_scores(df: pd.DataFrame, fair_rent: np.ndarray) -> pd.DataFrame:
    """Skor deal dari residual OUT-OF-FOLD pada skala log.

    Skala log dipilih karena error harga bersifat proporsional: salah Rp 2 jt pada unit Rp 3 jt
    jauh lebih besar daripada pada unit Rp 40 jt. Residual Rupiah mentah membuat unit mewah
    mendominasi simpangan baku sehingga unit murah hampir tidak pernah terdeteksi.
    z = (ln harga aktual - ln harga wajar model) / simpangan baku residual log.
    """
    df_eval = df.copy()
    df_eval["fair_market_rent_idr"] = np.round(fair_rent, 0)
    df_eval["residual_idr"] = df_eval["price_monthly_idr"] - df_eval["fair_market_rent_idr"]
    df_eval["residual_log"] = np.round(np.log(df_eval["price_monthly_idr"]) - np.log(fair_rent), 4)
    df_eval["discount_pct"] = np.round((df_eval["fair_market_rent_idr"] - df_eval["price_monthly_idr"]) / df_eval["fair_market_rent_idr"] * 100.0, 1)

    df_eval["deal_score_z"] = np.round(df_eval["residual_log"] / df_eval["residual_log"].std(ddof=1), 2)

    # classify_deal() diimpor dari deal_config -> ambang tidak ditulis ulang di sini.
    df_eval["deal_classification"] = df_eval["deal_score_z"].apply(classify_deal)
    df_eval["deal_tier"] = df_eval["deal_score_z"].apply(tier_of)
    return df_eval


AMENITY_FEATURES = ["is_full_furnished", "is_semi_furnished", "has_ac", "has_wifi", "has_water_heater",
                    "has_pool", "has_gym", "near_transit", "has_balcony", "has_kitchen", "has_parking"]


def empirical_interval(y_log: pd.Series, oof_log_repeats: np.ndarray, level: float = 0.80) -> Dict[str, float]:
    """Rentang prediksi EMPIRIS dari residual out-of-fold (gabungan semua pengulangan).

    Bukan interval statistik formal: ini sekadar "pada data kita, harga aktual jatuh di antara
    estimasi x lower_factor dan estimasi x upper_factor sebanyak `level` dari waktu".
    """
    resid = (y_log.values[None, :] - oof_log_repeats).ravel()
    lo, hi = np.quantile(resid, [(1 - level) / 2, 1 - (1 - level) / 2])
    return {"level": level, "log_lower": float(lo), "log_upper": float(hi),
            "lower_factor": float(np.exp(lo)), "upper_factor": float(np.exp(hi))}


def save_model_artifact(model, X: pd.DataFrame, df: pd.DataFrame, interval: Dict[str, float], path: str):
    """Simpan model final + semua yang dibutuhkan API agar memakai model yang SAMA dengan evaluasi."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump({
        "model": model,
        "feature_columns": list(X.columns),
        "cities": sorted(df["target_city"].unique()),
        "interval": interval,
        "n_train": int(len(X)),
        "trained_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }, path)


def build_market_summary(df_eval: pd.DataFrame, model, X: pd.DataFrame, metrics: Dict[str, Any],
                         audit: Dict[str, Any]) -> Dict[str, Any]:
    """Semua angka pasar yang dikutip README/UI/API. Dihitung dari data, tidak pernah diketik manual."""
    d = df_eval
    ppm2 = d["price_per_m2_idr"]
    tier = d.groupby("urban_zone")["price_per_m2_idr"].median()
    t1, t3 = tier.filter(like="Tier 1").iloc[0], tier.filter(like="Tier 3").iloc[0]

    raw_f = d[d.is_full_furnished == 1]["price_per_m2_idr"].median()
    raw_u = d[d.is_full_furnished == 0]["price_per_m2_idr"].median()
    X1, X0 = X.copy(), X.copy()
    X1["is_full_furnished"], X0["is_full_furnished"] = 1, 0
    adj = float(np.mean(np.exp(model.predict(X1) - model.predict(X0))) - 1) * 100

    z = d["deal_score_z"]
    flagged = d[is_below_estimate(z)]
    by_city = (d.groupby("target_city").agg(n=("listing_id", "count"), median_rent_idr=("price_monthly_idr", "median"),
               median_price_per_m2_idr=("price_per_m2_idr", "median")).reset_index()
               .sort_values("median_price_per_m2_idr", ascending=False))
    imputed = audit.get("geo_imputed_share_by_city", {})
    return {
        "n_units": int(len(d)), "n_cities": int(d["target_city"].nunique()),
        "median_rent_idr": float(d["price_monthly_idr"].median()),
        "median_price_per_m2_idr": float(ppm2.median()),
        "furnished_share_pct": round(float(d["is_full_furnished"].mean() * 100), 1),
        "tier1_vs_tier3_premium_pct": round(float((t1 / t3 - 1) * 100), 1),
        "furnishing_premium_raw_pct": round(float((raw_f / raw_u - 1) * 100), 1),
        "furnishing_premium_adjusted_pct": round(adj, 1),
        "deal_thresholds": deal_config.as_dict(),
        "deals": {
            "below_estimate_total": int(is_below_estimate(z).sum()),
            "below_estimate_share_pct": round(float(is_below_estimate(z).mean() * 100), 1),
            "deep": int(is_deep_value(z).sum()),
            "good": int((is_below_estimate(z) & ~is_deep_value(z)).sum()),
            "above_estimate_total": int((z >= PREMIUM_Z).sum()),
            "above_estimate_share_pct": round(float((z >= PREMIUM_Z).mean() * 100), 1),
            "median_discount_pct_of_flagged": round(float(flagged["discount_pct"].median()), 1) if len(flagged) else None,
        },
        "geo": {
            "imputed_share_pct": round(float(d["geo_is_imputed"].mean() * 100), 1),
            "imputed_share_pct_by_city": {k: round(v * 100, 1) for k, v in imputed.items()},
        },
        "by_city": by_city.round(0).to_dict(orient="records"),
        "audit": audit,
    }


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

    # 2. Evaluasi jujur (out-of-fold) + model final
    gb_model, metrics, oof_log_repeats = train_and_evaluate_models(df, X, y_log)
    oof_log_pred = oof_log_repeats.mean(axis=0)
    interval = empirical_interval(y_log, oof_log_repeats)
    metrics["prediction_interval"] = interval

    # 3. "Harga wajar" tiap listing = prediksi out-of-fold (model tidak pernah melihat listing itu)
    fair_rent = np.exp(oof_log_pred)
    df_evaluated = compute_deal_scores(df, fair_rent)

    # 3b. Simpan model final yang akan dipakai API + ringkasan pasar (sumber tunggal angka README/UI)
    save_model_artifact(gb_model, X, df, interval, os.path.join(base_dir, "models", "hedonic_gb.joblib"))
    audit_path = os.path.join(proc_dir, "pipeline_audit.json")
    audit = json.load(open(audit_path, encoding="utf-8")) if os.path.exists(audit_path) else {}
    summary = build_market_summary(df_evaluated, gb_model, X, metrics, audit)
    with open(os.path.join(proc_dir, "market_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

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