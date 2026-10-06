"""
backend/server.py
Production-grade FastAPI Backend for Household Intelligence PropTech Platform.
Adheres strictly to PRD v1.0 specifications and serves the modern Linear-themed frontend.
"""

import os
import json
import sqlite3
import joblib
import pandas as pd
import numpy as np
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "jabodetabek_rental_evaluated.csv")
DB_PATH = os.path.join(BASE_DIR, "data", "processed", "rental_intelligence.db")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
MODEL_PATH = os.path.join(BASE_DIR, "models", "hedonic_gb.joblib")
METRICS_PATH = os.path.join(BASE_DIR, "data", "processed", "model_evaluation_metrics.json")
SUMMARY_PATH = os.path.join(BASE_DIR, "data", "processed", "market_summary.json")

app = FastAPI(
    title="Household Intelligence API",
    description="PropTech Automated Valuation Model (AVM) and Deal Radar Telemetry Engine",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load evaluated dataset in memory for sub-millisecond querying
df = pd.read_csv(DATA_PATH)
df["discount_pct"] = df["discount_pct"].round(1)
df["residual_idr"] = df["residual_idr"].round(0)
df["deal_score_z"] = df["deal_score_z"].round(2)

for _p in (MODEL_PATH, METRICS_PATH, SUMMARY_PATH):
    if not os.path.exists(_p):
        raise RuntimeError(f"Artefak {_p} tidak ditemukan. Jalankan `python run_pipeline.py` dulu.")

ARTIFACT = joblib.load(MODEL_PATH)
MODEL = ARTIFACT["model"]
FEATURE_COLUMNS = ARTIFACT["feature_columns"]
INTERVAL = ARTIFACT["interval"]
with open(METRICS_PATH, encoding="utf-8") as _f:
    METRICS = json.load(_f)
with open(SUMMARY_PATH, encoding="utf-8") as _f:
    SUMMARY = json.load(_f)


class SimulationRequest(BaseModel):
    city: str = "Jakarta Selatan"
    subdistrict: Optional[str] = None
    floor_size_m2: float = 45.0
    bedrooms: int = 2
    bathrooms: int = 1
    distance_to_cbd_km: Optional[float] = None
    distance_to_transit_km: Optional[float] = None
    is_full_furnished: bool = True
    has_ac: bool = True
    has_pool: bool = True
    has_gym: bool = False
    has_balcony: bool = False
    has_kitchen: bool = True
    # Fitur tambahan yang ada di model (default False = tidak disebut di iklan)
    is_semi_furnished: bool = False
    has_wifi: bool = False
    has_water_heater: bool = False
    near_transit: bool = False
    has_parking: bool = False
    # ASUMSI pengguna (bukan hasil data): biaya fit-out per m2 untuk kalkulator payback
    fitout_cost_per_m2_idr: float = 1_200_000.0

@app.get("/api/telemetry")
def get_telemetry():
    """Metrik pasar & model. Semua angka dibaca dari artefak pipeline, tidak ada yang ditulis manual."""
    ev = METRICS["evaluation"]
    gb, naive, ridge = ev["kfold_5x3"]["gb"], ev["kfold_5x3"]["naive"], ev["kfold_5x3"]["ridge"]
    grp = ev["group_kfold_subdistrict"]
    deals = SUMMARY["deals"]
    return {
        "audited_units": SUMMARY["n_units"],
        "monitored_regions": SUMMARY["n_cities"],
        "median_rent_idr": SUMMARY["median_rent_idr"],
        "median_price_per_m2_idr": SUMMARY["median_price_per_m2_idr"],
        "furnished_share_pct": SUMMARY["furnished_share_pct"],
        "furnishing_premium_adjusted_pct": SUMMARY["furnishing_premium_adjusted_pct"],
        "furnishing_premium_raw_pct": SUMMARY["furnishing_premium_raw_pct"],
        "bargains_detected": deals["below_estimate_total"],
        "deep_value_count": deals["deep"],
        "good_deals_count": deals["good"],
        "below_estimate_share_pct": deals["below_estimate_share_pct"],
        "model": {
            "validation": "out-of-fold, KFold 5-lipat x3 pengulangan",
            "r2": gb["r2"], "mae_idr": gb["mae_idr"], "mape_pct": gb["mape_pct"],
            "median_ape_pct": gb["median_ape_pct"],
            "baseline_naive_r2": naive["r2"], "ridge_r2": ridge["r2"],
            "unseen_subdistrict_r2": grp["gb"]["r2"],
            "train_in_sample_r2_diagnostic": METRICS["train_in_sample_r2_DIAGNOSTIC_ONLY"],
            "top_features": METRICS["feature_importances"][:3],
            "interval_level": INTERVAL["level"],
            "interval_lower_factor": INTERVAL["lower_factor"],
            "interval_upper_factor": INTERVAL["upper_factor"],
        },
    }

@app.get("/api/listings")
def get_listings(
    city: Optional[str] = None,
    layout: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    is_furnished: Optional[bool] = None,
    only_deals: Optional[bool] = False,
    limit: int = 500
):
    """Query listings with optional multi-attribute filters."""
    filtered = df.copy()
    if city and city != "All":
        cities = [c.strip() for c in city.split(",") if c.strip()]
        if cities:
            filtered = filtered[filtered["target_city"].isin(cities)]
    if layout and layout != "All":
        layouts = [l.strip() for l in layout.split(",") if l.strip()]
        if layouts:
            filtered = filtered[filtered["layout_category"].isin(layouts)]
    if min_price is not None:
        filtered = filtered[filtered["price_monthly_idr"] >= min_price]
    if max_price is not None:
        filtered = filtered[filtered["price_monthly_idr"] <= max_price]
    if is_furnished:
        filtered = filtered[filtered["is_full_furnished"] == 1]
    if only_deals:
        filtered = filtered[filtered["deal_score_z"] <= -0.75]
    
    subset = filtered.head(limit)
    return {
        "count": len(subset),
        "total_matched": len(filtered),
        "data": subset.to_dict(orient="records"),
        "listings": subset.to_dict(orient="records")
    }

@app.get("/api/benchmarks")
def get_benchmarks():
    """District and City-level median price benchmarks."""
    city_bench = df.groupby("target_city").agg(
        median_rent_idr=("price_monthly_idr", "median"),
        median_price_per_m2_idr=("price_per_m2_idr", "median"),
        mean_price_per_m2_idr=("price_per_m2_idr", "mean"),
        sample_size=("listing_id", "count"),
        median_distance_cbd=("distance_to_cbd_km", "median"),
        median_distance_transit=("distance_to_transit_km", "median"),
        furnished_pct=("is_full_furnished", lambda x: round(x.mean() * 100, 1))
    ).reset_index().sort_values("median_price_per_m2_idr", ascending=False)
    
    layout_bench = df.groupby("layout_category").agg(
        sample_size=("listing_id", "count"),
        median_rent_idr=("price_monthly_idr", "median"),
        median_size_m2=("floor_size_m2", "median")
    ).reset_index().sort_values("median_rent_idr", ascending=True)

    return {
        "cities": city_bench.to_dict(orient="records"),
        "layouts": layout_bench.to_dict(orient="records")
    }

@app.get("/api/deals")
def get_deals(tier: str = "all", limit: int = 50):
    """Curated Deal Hunter listings ranked by standardized statistical residual."""
    deals = df[df["deal_score_z"] <= -0.75].copy()
    if tier == "deep":
        deals = deals[deals["deal_score_z"] <= -1.5]
    elif tier == "good":
        deals = deals[(deals["deal_score_z"] > -1.5) & (deals["deal_score_z"] <= -0.75)]
    
    deals = deals.sort_values("deal_score_z").head(limit)
    return {
        "total_deals": len(deals),
        "tier": tier,
        "deals": deals.to_dict(orient="records")
    }

@app.get("/api/districts")
def get_districts(city: Optional[str] = None):
    """Aggregate real property listings by administrative subdistrict / kawasan."""
    dff = df.copy()
    if city and city != "All":
        dff = dff[dff["target_city"] == city]
    
    dist = dff.groupby(["target_city", "subdistrict"]).agg(
        unit_count=("listing_id", "count"),
        median_rent_idr=("price_monthly_idr", "median"),
        median_price_per_m2_idr=("price_per_m2_idr", "median"),
        deals_count=("deal_score_z", lambda z: (z <= -0.75).sum()),
        latitude=("latitude", "mean"),
        longitude=("longitude", "mean")
    ).reset_index().sort_values("unit_count", ascending=False)

    return {
        "total_districts": len(dist),
        "districts": dist.to_dict(orient="records")
    }

def _area_default(req: SimulationRequest, col: str, fallback: float) -> float:
    """Median jarak per subdistrik (jika diketahui), lalu median kota, lalu fallback."""
    scope = df[df["target_city"] == req.city]
    if req.subdistrict:
        sub = scope.loc[scope["subdistrict"] == req.subdistrict, col]
        if not sub.empty:
            return float(sub.median())
    return float(scope[col].median()) if not scope.empty else fallback


def _feature_row(req: SimulationRequest, cbd_km: float, transit_km: float) -> pd.DataFrame:
    """Susun satu baris fitur persis seperti build_hedonic_features() di pipeline training."""
    row = {c: 0.0 for c in FEATURE_COLUMNS}
    row.update({
        "log_floor_size": float(np.log(req.floor_size_m2)),
        "bedrooms": req.bedrooms, "bathrooms": req.bathrooms,
        "distance_to_cbd_km": cbd_km, "distance_to_transit_km": transit_km,
        "is_full_furnished": int(req.is_full_furnished), "is_semi_furnished": int(req.is_semi_furnished),
        "has_ac": int(req.has_ac), "has_wifi": int(req.has_wifi), "has_water_heater": int(req.has_water_heater),
        "has_pool": int(req.has_pool), "has_gym": int(req.has_gym), "near_transit": int(req.near_transit),
        "has_balcony": int(req.has_balcony), "has_kitchen": int(req.has_kitchen), "has_parking": int(req.has_parking),
    })
    dummy = f"city_{req.city}"
    if dummy in row:          # kota baseline (drop_first) tidak punya kolom dummy
        row[dummy] = 1.0
    return pd.DataFrame([row], columns=FEATURE_COLUMNS)


@app.post("/api/simulate")
def simulate_rent(req: SimulationRequest):
    """Estimasi harga sewa wajar dari model Gradient Boosting yang SAMA dengan yang dievaluasi.

    Rentang = kuantil empiris residual out-of-fold (bukan interval statistik formal).
    Analisis furnishing = selisih prediksi model dengan/ tanpa flag furnished (ceteris paribus),
    dan biaya fit-out adalah asumsi pengguna.
    """
    if req.city not in ARTIFACT["cities"]:
        raise HTTPException(status_code=400, detail=f"Kota tidak dikenal: {req.city}. Pilihan: {ARTIFACT['cities']}")
    if not (15 <= req.floor_size_m2 <= 350):
        raise HTTPException(status_code=400, detail="floor_size_m2 harus di antara 15 dan 350 (rentang data latih).")

    cbd_km = req.distance_to_cbd_km if req.distance_to_cbd_km is not None else _area_default(req, "distance_to_cbd_km", 8.0)
    transit_km = req.distance_to_transit_km if req.distance_to_transit_km is not None else _area_default(req, "distance_to_transit_km", 1.5)

    fair = float(np.exp(MODEL.predict(_feature_row(req, cbd_km, transit_km))[0]))
    est_fair_rent = round(fair / 50_000) * 50_000
    ci_lower = round(fair * INTERVAL["lower_factor"] / 50_000) * 50_000
    ci_upper = round(fair * INTERVAL["upper_factor"] / 50_000) * 50_000

    # Premi furnished ceteris paribus: prediksi (full furnished) - prediksi (tidak full furnished)
    on, off = req.model_copy(update={"is_full_furnished": True}), req.model_copy(update={"is_full_furnished": False})
    rent_on = float(np.exp(MODEL.predict(_feature_row(on, cbd_km, transit_km))[0]))
    rent_off = float(np.exp(MODEL.predict(_feature_row(off, cbd_km, transit_km))[0]))
    premium_monthly = max(rent_on - rent_off, 0.0)
    fitout_cost = req.floor_size_m2 * req.fitout_cost_per_m2_idr
    payback_months = round(fitout_cost / premium_monthly, 1) if premium_monthly > 0 else None

    city_base = float(df.loc[df["target_city"] == req.city, "price_per_m2_idr"].median())
    return {
        "fair_market_rent_idr": float(est_fair_rent),
        "ci_lower_idr": float(ci_lower),
        "ci_upper_idr": float(ci_upper),
        "interval_level_pct": int(INTERVAL["level"] * 100),
        "implicit_rate_per_m2_idr": float(round(est_fair_rent / req.floor_size_m2)),
        "city_benchmark_rate_m2": city_base,
        "inputs_used": {"distance_to_cbd_km": round(cbd_km, 2), "distance_to_transit_km": round(transit_km, 2)},
        "furnishing_analysis": {
            "unfurnished_baseline_idr": float(round(rent_off)),
            "monthly_extra_cashflow_idr": float(round(premium_monthly)),
            "annual_extra_cashflow_idr": float(round(premium_monthly * 12)),
            "estimated_fitout_cost_idr": float(fitout_cost),
            "fitout_cost_is_user_assumption": True,
            "payback_period_months": payback_months,
            "payback_period_years": round(payback_months / 12, 1) if payback_months is not None else None,
        },
    }

@app.get("/api/distance-decay")
def get_distance_decay():
    """Data for the Alonso-Muth-Mills urban rent decay model."""
    sample = df[["distance_to_cbd_km", "distance_to_transit_km", "price_per_m2_idr", "target_city", "urban_zone"]].dropna()
    sample = sample[sample["price_per_m2_idr"] <= 600_000].head(400)
    
    zones = df.groupby("urban_zone").agg(
        sample_units=("listing_id", "count"),
        median_price_per_m2=("price_per_m2_idr", "median"),
        mean_price_per_m2=("price_per_m2_idr", "mean"),
        median_rent_monthly=("price_monthly_idr", "median"),
        median_dist_cbd=("distance_to_cbd_km", "median")
    ).reset_index().to_dict(orient="records")

    return {
        "points": sample.to_dict(orient="records"),
        "zones": zones
    }

@app.get("/apartemen")
def fallback_tutorial_apartemen():
    """Fallback endpoint for backward compatibility with learning tutorial tabs."""
    sample = df[["listing_id", "title", "price_monthly_idr"]].head(10).to_dict(orient="records")
    return {"status": "sukses", "total": len(sample), "data": sample}

# Mount static frontend
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
def serve_index():
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Frontend not built yet. API is running."}