"""
backend/server.py
Production-grade FastAPI Backend for Household Intelligence PropTech Platform.
Adheres strictly to PRD v1.0 specifications and serves the modern Linear-themed frontend.
"""

import os
import sys
import json
import secrets
import threading
import joblib
import pandas as pd
import numpy as np
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse, HTMLResponse
from pydantic import BaseModel
from typing import Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "src")
DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "jabodetabek_rental_evaluated.csv")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
MODEL_PATH = os.path.join(BASE_DIR, "models", "hedonic_gb.joblib")
METRICS_PATH = os.path.join(BASE_DIR, "data", "processed", "model_evaluation_metrics.json")
SUMMARY_PATH = os.path.join(BASE_DIR, "data", "processed", "market_summary.json")

# Ambang klasifikasi deal: satu sumber kebenaran yang dipakai juga oleh pipeline
# dan (lewat /api/telemetry) oleh frontend. Jangan hardcode angka di file lain.
sys.path.insert(0, SRC_DIR)
import deal_config  # noqa: E402
from deal_config import is_below_estimate, matches_tier  # noqa: E402


def _is_production() -> bool:
    return (os.getenv("VERCEL_ENV", "").strip() == "production"
            or os.getenv("HI_ENV", "").strip().lower() == "production"
            or os.getenv("ENV", "").strip().lower() == "production")


# Frontend memakai path relatif (`/api/...`), jadi aplikasi selalu same-origin dan
# TIDAK butuh CORS. Default = tidak ada origin lintas-domain yang diizinkan;
# set ALLOWED_ORIGINS (dipisah koma) bila frontend disajikan dari domain lain.
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]
if not ALLOWED_ORIGINS and not _is_production():
    # Kenyamanan pengembangan lokal: izinkan loopback (mis. frontend di :5500).
    ALLOWED_ORIGINS = [f"http://{host}:{port}"
                       for host in ("localhost", "127.0.0.1")
                       for port in (5500, 8000, 8080, 8791)]

# Endpoint maintenance yang memutasi state in-memory; dinonaktifkan sampai
# HI_ADMIN_TOKEN diisi. Sebelumnya endpoint ini terbuka untuk siapa saja.
ADMIN_TOKEN = os.getenv("HI_ADMIN_TOKEN", "").strip()
_reload_lock = threading.Lock()

app = FastAPI(
    title="Household Intelligence API",
    description="PropTech Automated Valuation Model (AVM) and Deal Radar Telemetry Engine",
    version="1.0.0"
)

# Payload /api/listings ~2.3 MB tanpa kompresi; gzip memangkasnya ke seperempatnya.
app.add_middleware(GZipMiddleware, minimum_size=1024)

if ALLOWED_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=False,  # tidak ada auth berbasis cookie di aplikasi ini
        allow_methods=["GET", "POST", "HEAD", "OPTIONS"],
        allow_headers=["Content-Type", "X-Admin-Token"],
    )

# Load evaluated dataset in memory for sub-millisecond querying
def load_dataset():
    global df
    df = pd.read_csv(DATA_PATH)
    df["discount_pct"] = df["discount_pct"].round(1)
    df["residual_idr"] = df["residual_idr"].round(0)
    df["deal_score_z"] = df["deal_score_z"].round(2)
    # Kolom resolver boleh null (unresolved = tidak ada nama karangan).
    # NaN -> None supaya JSON response valid.
    for col in df.columns:
        if not pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].astype(object).where(df[col].notna(), None)
    return df

df = load_dataset()


def _cbd_decay_per_5km(frame: pd.DataFrame) -> float:
    """Kemiringan log-linear harga/m2 terhadap jarak ke CBD, dinyatakan per 5 km.

    Dipakai untuk dokumentasi mesin (llms.txt) supaya angkanya dihitung dari data,
    bukan ditulis manual. Klaim manual sebelumnya ("12.4% per 5 km") meleset 2.3x
    dari nilai sebenarnya.
    """
    s = frame[["distance_to_cbd_km", "price_per_m2_idr"]].dropna()
    s = s[s["price_per_m2_idr"].between(10_000, 600_000)]
    if len(s) < 30:
        return 0.0
    slope = float(np.polyfit(s["distance_to_cbd_km"], np.log(s["price_per_m2_idr"]), 1)[0])
    return round((np.exp(slope * 5) - 1) * 100, 1)


CBD_DECAY_PER_5KM_PCT = _cbd_decay_per_5km(df)


@app.api_route("/api/reload-data", methods=["GET", "POST"])
def reload_data(x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token")):
    """Muat ulang dataset ke memori. Butuh header X-Admin-Token (env HI_ADMIN_TOKEN)."""
    if not ADMIN_TOKEN:
        raise HTTPException(
            status_code=403,
            detail="Endpoint maintenance dinonaktifkan. Set env HI_ADMIN_TOKEN untuk mengaktifkannya.",
        )
    if not x_admin_token or not secrets.compare_digest(x_admin_token, ADMIN_TOKEN):
        raise HTTPException(status_code=401, detail="Token admin tidak valid.")
    with _reload_lock:
        load_dataset()
        return {
            "status": "success",
            "total_listings": len(df),
            "sample_title": df.iloc[0]["title"],
        }


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
    has_ac: bool = False
    has_pool: bool = True
    has_gym: bool = False
    has_balcony: bool = False
    has_kitchen: bool = False
    # Fitur tambahan yang ada di model (default False = tidak disebut di iklan)
    is_semi_furnished: bool = False
    has_wifi: bool = False
    has_water_heater: bool = False
    near_transit: bool = False
    has_parking: bool = False
    # ASUMSI pengguna (bukan hasil data): biaya fit-out per m2 untuk kalkulator payback
    fitout_cost_per_m2_idr: float = 1_200_000.0

@app.api_route("/api/telemetry", methods=["GET", "HEAD"])
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
        # Konsisten dengan /api/districts: satu distrik dihitung per (kota, kawasan).
        "monitored_districts": int(df.groupby(["target_city", "subdistrict"]).ngroups),
        # Frontend WAJIB memakai angka ini, bukan literal sendiri: sebelumnya UI
        # memakai -1.2 sehingga 29 unit salah label sebagai "Deep Value".
        "deal_thresholds": deal_config.as_dict(),
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

@app.api_route("/api/listings", methods=["GET", "HEAD"])
def get_listings(
    city: Optional[str] = None,
    layout: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    is_furnished: Optional[bool] = None,
    only_deals: bool = False,
    sort_by: str = "deal_score_z",
    limit: int = 800
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
            conds = []
            for l in layouts:
                if l.upper() == "STUDIO":
                    conds.append(filtered["bedrooms"] == 0)
                elif l.upper() == "1BR":
                    conds.append(filtered["bedrooms"] == 1)
                elif l.upper() == "2BR":
                    conds.append((filtered["bedrooms"] == 2) | (filtered["layout_category"] == "2 Bedroom"))
                elif l.upper() == "3BR":
                    conds.append((filtered["bedrooms"] == 3) | (filtered["layout_category"] == "3 Bedroom"))
                elif l.upper() in ["4BR+", "4BR"]:
                    conds.append((filtered["bedrooms"] >= 4) | (filtered["layout_category"] == "4+ Bedroom"))
                else:
                    conds.append(filtered["layout_category"] == l)
            if conds:
                combined_cond = conds[0]
                for c in conds[1:]:
                    combined_cond = combined_cond | c
                filtered = filtered[combined_cond]
    if min_price is not None:
        filtered = filtered[filtered["price_monthly_idr"] >= min_price]
    if max_price is not None:
        filtered = filtered[filtered["price_monthly_idr"] <= max_price]
    if is_furnished:
        filtered = filtered[filtered["is_full_furnished"] == 1]
    if only_deals:
        filtered = filtered[is_below_estimate(filtered["deal_score_z"])]
    
    subset = filtered.head(limit)
    return {
        "count": len(subset),
        "total_matched": len(filtered),
        "data": subset.to_dict(orient="records"),
    }

@app.api_route("/api/benchmarks", methods=["GET", "HEAD"])
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

@app.api_route("/api/deals", methods=["GET", "HEAD"])
def get_deals(tier: str = "all", limit: int = 50):
    """Curated Deal Hunter listings ranked by standardized statistical residual."""
    try:
        matched = df[matches_tier(df["deal_score_z"], tier)].copy()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    matched = matched.sort_values("deal_score_z")
    deals = matched.head(limit)
    return {
        # total_deals = seluruh unit yang cocok (bukan ukuran halaman), sejalan
        # dengan total_matched/count di /api/listings.
        "total_deals": int(len(matched)),
        "count": int(len(deals)),
        "limit": limit,
        "tier": tier,
        "thresholds": deal_config.as_dict(),
        "deals": deals.to_dict(orient="records")
    }

@app.api_route("/api/districts", methods=["GET", "HEAD"])
def get_districts(city: Optional[str] = None):
    """Aggregate real property listings by administrative subdistrict / kawasan."""
    dff = df.copy()
    if city and city != "All":
        dff = dff[dff["target_city"] == city]
    
    dist = dff.groupby(["target_city", "subdistrict"]).agg(
        unit_count=("listing_id", "count"),
        median_rent_idr=("price_monthly_idr", "median"),
        median_price_per_m2_idr=("price_per_m2_idr", "median"),
        deals_count=("deal_score_z", lambda z: int(is_below_estimate(z).sum())),
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


# Premi furnishing & amenitas. Dipakai sebagai penjaga monotonisitas karena model
# pohon tidak menjamin arah efek (terbukti: model memprediksi semi-furnished LEBIH
# MURAH dari unfurnished, dan kamar mandi tambahan justru menurunkan harga).
# Angka ini dipakai HANYA sebagai faktor ceteris paribus di atas prediksi dengan
# amenitas dinetralkan.
def _furnishing_premium_full() -> float:
    """Ambil premi furnished dari telemetry pipeline (audited), bukan angka ketik manual."""
    pct = SUMMARY.get("furnishing_premium_adjusted_pct")
    return float(pct) / 100.0 if isinstance(pct, (int, float)) else 0.139


FURNISHING_PREMIUM_SEMI = 0.060        # asumsi konservatif: separuh dari premium full
BATHROOM_PREMIUM_PER_EXTRA = 0.035     # ensuite / kamar mandi tamu
AMENITY_PREMIUMS = {                   # ceteris paribus: amenitas tidak pernah menurunkan sewa
    "has_pool": 0.03,
    "has_gym": 0.02,
    "near_transit": 0.05,
    "has_balcony": 0.02,
    "has_parking": 0.02,
}

# Toleransi luas saat mencari listing pembanding untuk indikator dukungan data.
COMPARABLE_SIZE_TOLERANCE = 0.25


def _data_support(req: SimulationRequest) -> dict:
    """Seberapa kuat data nyata mendukung estimasi ini.

    Model pohon bisa mengekstrapolasi diam-diam ke kombinasi kamar/luas yang tidak
    ada di dataset. Angka ini menggantikan kepercayaan palsu: berapa listing nyata
    di kota yang sama dengan jumlah kamar sama dan luas dalam +/-25%, plus rentang
    luas yang benar-benar teramati (persentil 5-95) untuk jumlah kamar itu.
    """
    city_scope = df[df["target_city"] == req.city]
    same_beds = city_scope[city_scope["bedrooms"] == req.bedrooms]
    scope_label = "city"
    if len(same_beds) < 5:
        same_beds = df[df["bedrooms"] == req.bedrooms]
        scope_label = "national"

    lo = req.floor_size_m2 * (1 - COMPARABLE_SIZE_TOLERANCE)
    hi = req.floor_size_m2 * (1 + COMPARABLE_SIZE_TOLERANCE)
    comparables = same_beds[same_beds["floor_size_m2"].between(lo, hi)]

    size_range = None
    inside_range = None
    if len(same_beds) >= 10:
        q05 = float(same_beds["floor_size_m2"].quantile(0.05))
        q95 = float(same_beds["floor_size_m2"].quantile(0.95))
        size_range = [round(q05), round(q95)]
        inside_range = bool(q05 <= req.floor_size_m2 <= q95)

    matched = int(len(comparables))
    if matched >= 5:
        support_level = "strong"
    elif matched >= 1:
        support_level = "limited"
    else:
        # Tidak ada satu pun unit mirip di data: angka ini murni ekstrapolasi model.
        support_level = "extrapolated"

    return {
        "support_level": support_level,
        "comparables_matched": matched,
        "same_bedrooms_available": int(len(same_beds)),
        "scope": scope_label,
        "typical_size_range_m2": size_range,
        "inside_typical_size_range": inside_range,
        "median_comparable_rent_idr": (
            float(comparables["price_monthly_idr"].median()) if matched else None
        ),
    }


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

    # 1. Prediksi dasar: prediksi model untuk KONFIGURASI YANG DIMINTA, dengan
    #    amenitas dinetralkan. Premi furnishing/amenitas ditambahkan terpisah di
    #    bawah (ceteris paribus), jadi tidak dihitung dua kali.
    #
    #    CATATAN PERBAIKAN (penting): sampai commit ini, di sini ada loop
    #    "enforce hedonic monotonicity" yang mengambil max() prediksi untuk SEMUA
    #    jumlah kamar yang lebih kecil pada luas yang sama. Model ini menilai unit
    #    dengan kamar lebih sedikit pada luas yang sama sebagai unit yang lebih
    #    premium - dan itu memang struktur pasar Jakarta: di Jakarta Selatan 1BR
    #    median 60 m2 sedangkan 2BR median 94 m2, dua produk berbeda.
    #
    #    Efek loop itu: permintaan 2BR 70 m2 dijawab dengan prediksi studio 70 m2,
    #    keluar Rp 28,25 juta padahal median harga aktual segmen itu Rp 17,0 juta
    #    (+64%). Modelnya sendiri terkalibrasi: prediksi out-of-fold di segmen
    #    JakSel 2BR 55-90 m2 hanya +8,5% dari harga aktual (median APE 18,6%,
    #    sejalan dengan median APE global 17,7%). Jadi kelebihan itu berasal dari
    #    loop, bukan dari model.
    #
    #    Alternatifnya adalah melatih ulang dengan monotonic_cst. Sudah diukur:
    #    R2 out-of-fold turun dari 0,8298 ke 0,7634 (-6,6 poin) dan MAE naik 17%,
    #    jadi tidak diambil. Monotonisitas yang benar-benar dilalui pengguna dijaga
    #    di jalur UX: UI menyinkronkan luas ke ukuran tipikal saat jumlah kamar
    #    diubah (BEDROOM_PRESETS di simulator.js) dan memberi peringatan bila luas
    #    di luar rentang realistis.
    clean_req = req.model_copy(update={
        "bathrooms": 1,
        "is_full_furnished": False, "is_semi_furnished": False,
        "has_ac": False, "has_wifi": False, "has_water_heater": False,
        "has_pool": False, "has_gym": False, "near_transit": False,
        "has_balcony": False, "has_kitchen": False, "has_parking": False
    })
    base_fair = float(np.exp(MODEL.predict(_feature_row(clean_req, cbd_km, transit_km))[0]))

    # Bathroom utility: kamar mandi tambahan (ensuite / powder room tamu) memberi
    # utilitas monoton.
    extra_baths = max(0, req.bathrooms - 1)
    base_fair = base_fair * (1.0 + extra_baths * BATHROOM_PREMIUM_PER_EXTRA)

    # 2. Objective subdistrict micro-market index calibration
    # Anchors valuation to real neighborhood price per m2 without relying on arbitrary Sudirman distance
    scope = df[df["target_city"] == req.city]
    city_med = float(scope["price_per_m2_idr"].median()) if not scope.empty else 120_000.0
    if req.subdistrict:
        sub_scope = scope[scope["subdistrict"] == req.subdistrict]
        if not sub_scope.empty and city_med > 0:
            sub_med = float(sub_scope["price_per_m2_idr"].median())
            sub_ratio = sub_med / city_med
            clamped_ratio = max(0.65, min(1.65, sub_ratio))
            base_fair = base_fair * (0.35 + 0.65 * clamped_ratio)

    # 3. Furnishing condition multiplier (Full: dari telemetry pipeline, Semi: +6.0%, Unfurnished: 1.0x)
    premium_full = _furnishing_premium_full()
    if req.is_full_furnished:
        furnishing_multiplier = 1.0 + premium_full
    elif req.is_semi_furnished:
        furnishing_multiplier = 1.0 + FURNISHING_PREMIUM_SEMI
    else:
        furnishing_multiplier = 1.000

    # 4. Monotonic physical & building amenities premiums (ceteris paribus: amenities never reduce property rent)
    amenity_multiplier = 1.0
    for flag, premium in AMENITY_PREMIUMS.items():
        if getattr(req, flag, False):
            amenity_multiplier += premium

    fair = base_fair * furnishing_multiplier * amenity_multiplier

    est_fair_rent = round(fair / 50_000) * 50_000
    ci_lower = round(fair * INTERVAL["lower_factor"] / 50_000) * 50_000
    ci_upper = round(fair * INTERVAL["upper_factor"] / 50_000) * 50_000

    # Premi furnished ceteris paribus: full furnished vs unfurnished baseline
    rent_off = base_fair * 1.0 * amenity_multiplier
    rent_on = base_fair * (1.0 + premium_full) * amenity_multiplier
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
        "data_support": _data_support(req),
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

HEDONIC_PATH = os.path.join(BASE_DIR, "data", "processed", "hedonic_implicit_prices.json")
SHAP_PATH = os.path.join(BASE_DIR, "data", "processed", "shap_gb_summary.json")


@app.api_route("/api/shap", methods=["GET", "HEAD"])
def get_shap():
    """SHAP untuk model GB (read-only; jalankan `python src/shap_gb.py` untuk regenerate)."""
    if not os.path.exists(SHAP_PATH):
        raise HTTPException(status_code=503, detail="shap_gb_summary.json belum ada; jalankan `python src/shap_gb.py`.")
    with open(SHAP_PATH, encoding="utf-8") as f:
        return json.load(f)


@app.api_route("/api/hedonic", methods=["GET", "HEAD"])
def get_hedonic():
    """Implicit price per fitur (OLS log-rent, HC1, CI 95%). Interpretasi, bukan prediksi."""
    if not os.path.exists(HEDONIC_PATH):
        raise HTTPException(status_code=503, detail="hedonic_implicit_prices.json belum ada; jalankan pipeline.")
    with open(HEDONIC_PATH, encoding="utf-8") as f:
        return json.load(f)


@app.api_route("/api/distance-decay", methods=["GET", "HEAD"])
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

@app.api_route("/apartemen", methods=["GET", "HEAD"])
def fallback_tutorial_apartemen():
    """Fallback endpoint for backward compatibility with learning tutorial tabs."""
    sample = df[["listing_id", "title", "price_monthly_idr"]].head(10).to_dict(orient="records")
    return {"status": "sukses", "total": len(sample), "data": sample}

# Mount static frontend
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
    css_dir = os.path.join(FRONTEND_DIR, "css")
    if os.path.exists(css_dir):
        app.mount("/css", StaticFiles(directory=css_dir), name="css")
    js_dir = os.path.join(FRONTEND_DIR, "js")
    if os.path.exists(js_dir):
        app.mount("/js", StaticFiles(directory=js_dir), name="js")

@app.api_route("/robots.txt", methods=["GET", "HEAD"], response_class=PlainTextResponse)
def serve_robots():
    return "User-agent: *\nAllow: /\n\nSitemap: /llms.txt\n"

@app.api_route("/llms.txt", methods=["GET", "HEAD"], response_class=PlainTextResponse)
def serve_llms_txt():
    return f"""# Household Intelligence — Greater Jakarta Rental Housing & Market Intelligence Engine

> Author: Afiatta Ilhan Saleh
> Repository: https://github.com/Lottoenergon/Household-Intelligence
> Stack: FastAPI, Python, scikit-learn (GradientBoostingRegressor), SQLite Star Schema, Vanilla JS/CSS

## Overview
Household Intelligence is an end-to-end PropTech analytics platform and Automated Valuation Model (AVM) tracking {SUMMARY['n_units']} audited residential rental units across {SUMMARY['n_cities']} Greater Jakarta (Jabodetabek) cities.

## Core Analytics Modules
1. **Rental Deal Radar**: Identifies undervalued listings priced below statistical fair market value using a hedonic gradient boosting regression model.
2. **Smart Rent Valuation Calculator**: Real-time hedonic valuation based on unit floor size, micro-district indexing, room counts, and furnishing tiers.
3. **Urban Spatial Decay (Alonso-Muth-Mills)**: Models rental decay away from the Sudirman CBD ({CBD_DECAY_PER_5KM_PCT:.1f}% per 5 km, diukur log-linear pada harga/m² vs jarak ke CBD, n={len(df)}).
4. **Investor Capital Allocation & Fit-Out Payback**: Estimates cashflow yield and break-even payback period for furnishing interior renovations.

## Machine-Readable API Endpoints
- `GET /api/telemetry` — High-level market metrics, unit counts, and audited benchmarks.
- `GET /api/listings` — Audited listing catalog with fair value discount deltas.
- `GET /api/deals?tier=all|deep|good` — Top underpriced apartment listings ranked by discount percentage.
- `GET /api/districts?city=` — Per-subdistrict aggregates with unit counts and deal counts.
- `GET /api/benchmarks` — City and layout-level median rent / price-per-m² benchmarks.
- `POST /api/simulate` — Real-time hedonic rent simulation engine.
- `GET /api/hedonic` — OLS log-rent implicit prices per attribute (% effect, 95% CI, HC1 SE). For interpretation, not valuation.
- `GET /api/distance-decay` — Spatial rent decay curve vs distance to Sudirman CBD plus urban-zone rings.
"""

@app.api_route("/overview", methods=["GET", "HEAD"], response_class=HTMLResponse)
@app.api_route("/llm", methods=["GET", "HEAD"], response_class=HTMLResponse)
def serve_overview():
    summary_text = serve_llms_txt()
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Household Intelligence • LLM & Architecture Overview</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 860px; margin: 40px auto; padding: 0 24px; line-height: 1.6; color: #111; background: #fff; }}
        pre {{ background: #f6f8fa; padding: 20px; border-radius: 8px; border: 1px solid #e1e4e8; overflow-x: auto; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 14px; white-space: pre-wrap; }}
        a {{ color: #0366d6; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <h1>Household Intelligence Overview</h1>
    <p>Machine-readable documentation for AI crawlers, LLMs, and PropTech researchers.</p>
    <pre>{summary_text}</pre>
</body>
</html>"""
    return HTMLResponse(content=html)

@app.api_route("/", methods=["GET", "HEAD"])
def serve_index():
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Frontend not built yet. API is running."}