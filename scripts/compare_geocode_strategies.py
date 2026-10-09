"""Bandingkan 4 strategi penempatan koordinat project (Nominatim) di level model.

Tujuan: memilih kebijakan imputasi mana yang memberi R2/MAPE terbaik, bukan
menebak. Semua varian dievaluasi dengan protokol OOF yang sama
(GroupKFold by subdistrict + KFold 5x3) lewat market_intelligence.

Varian:
  A. baseline        : apa adanya (listing -> subdistrict -> city)
  B. project_fill    : project coords hanya mengisi listing yang belum punya koord
  C. project_override: project coords menggantikan SEMUA koord (termasuk pin portal)
  D. hybrid          : override HANYA listing yang pin-nya menyimpang >THRESH km dari
                       titik project lain di project yang sama (buang outlier broker)
"""
import json
import os
import sys

import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from entity_resolution import resolve  # noqa: E402
from transformation import JAKARTA_CBD_COORDS, KEY_TRANSIT_HUBS, haversine_distance_km  # noqa: E402
from market_intelligence import build_hedonic_features, train_and_evaluate_models  # noqa: E402

CLEANED = os.path.join(BASE_DIR, "data", "processed", "jabodetabek_rental_cleaned.csv")
PROJ_COORDS = os.path.join(BASE_DIR, "data", "project_coordinates.json")
OUT = os.path.join(BASE_DIR, "data", "processed", "geocode_strategy_comparison.json")


def load():
    df = pd.read_csv(CLEANED)
    proj = json.load(open(PROJ_COORDS, encoding="utf-8"))
    return df, proj


def resolve_pids(df):
    pids = []
    for t, u in zip(df["title"], df["url"]):
        pids.append(resolve(t, u).get("project_id"))
    return pids


def recompute_spatial(df):
    """Hitung ulang jarak CBD & transit dari latitude/longitude saat ini."""
    cbd_lat, cbd_lon = JAKARTA_CBD_COORDS
    df = df.copy()
    df["distance_to_cbd_km"] = [
        haversine_distance_km(a, b, cbd_lat, cbd_lon)
        for a, b in zip(df["latitude"], df["longitude"])
    ]
    hub_names, hub_dists = [], []
    for a, b in zip(df["latitude"], df["longitude"]):
        dists = {n: haversine_distance_km(a, b, tl, tn) for n, (tl, tn) in KEY_TRANSIT_HUBS.items()}
        best = min(dists.keys(), key=lambda k: dists[k])
        hub_names.append(best)
        hub_dists.append(dists[best])
    df["nearest_transit_hub"] = hub_names
    df["distance_to_transit_km"] = hub_dists
    return df


def apply_variant(df, proj, mode, pid_series, thresh_km=5.0, anchor_source="median_portal"):
    """Kembalikan dataframe baru dengan koordinat sesuai strategi.

    anchor_source: titik acuan per project = 'nominatim' (koord gedung OSM) atau
    'median_portal' (median koord listing portal)
    """
    out = df.copy()
    out["project_id"] = pid_series

    # Titik acuan per project
    if anchor_source == "nominatim":
        anchors = {pid: (v["lat"], v["lon"]) for pid, v in proj.items()}
    else:
        portal = out[(out["geo_source"] == "listing") & out["project_id"].notna()]
        anchors = portal.groupby("project_id")[["latitude", "longitude"]].median().apply(
            lambda r: (r["latitude"], r["longitude"]), axis=1).to_dict()

    for idx, row in out.iterrows():
        pid = row["project_id"]
        if not pid or pid not in anchors:
            continue
        alat, alon = anchors[pid]
        cur_lat, cur_lon = row["latitude"], row["longitude"]
        is_real = row["geo_source"] == "listing" and not pd.isna(cur_lat)

        if mode == "project_fill":
            if not is_real:
                out.at[idx, "latitude"], out.at[idx, "longitude"] = alat, alon
                out.at[idx, "geo_source"] = "project_geocoded"
        elif mode == "project_override":
            out.at[idx, "latitude"], out.at[idx, "longitude"] = alat, alon
            out.at[idx, "geo_source"] = "project_geocoded"
        elif mode == "hybrid":
            if is_real:
                dist = haversine_distance_km(cur_lat, cur_lon, alat, alon)
                if dist > thresh_km:
                    # pin broker menyimpang jauh -> ganti dengan titik project
                    out.at[idx, "latitude"], out.at[idx, "longitude"] = alat, alon
                    out.at[idx, "geo_source"] = "project_geocentered"
            else:
                out.at[idx, "latitude"], out.at[idx, "longitude"] = alat, alon
                out.at[idx, "geo_source"] = "project_geocoded"
    return out


def evaluate(df, label, pid_series):
    d = df.dropna(subset=["latitude", "longitude"]).copy()
    d = recompute_spatial(d)
    X, y_log, _ = build_hedonic_features(d)
    _, metrics, _ = train_and_evaluate_models(d, X, y_log)
    gb = metrics["evaluation"]["kfold_5x3"]["gb"]
    grp = metrics["evaluation"]["group_kfold_subdistrict"]["gb"]
    res = {
        "variant": label,
        "n": int(len(d)),
        "kfold_r2": round(gb["r2"], 4),
        "kfold_mae": round(gb["mae_idr"], 0),
        "kfold_mape": round(gb["mape_pct"], 2),
        "kfold_medape": round(gb["median_ape_pct"], 2),
        "group_r2": round(grp["r2"], 4),
        "group_mape": round(grp["mape_pct"], 2),
        "geo_counts": d["geo_source"].value_counts().to_dict(),
    }
    print(json.dumps(res, indent=2), flush=True)
    return res


def main():
    df, proj = load()
    pids = resolve_pids(df)
    df["project_id"] = pids
    print(f"projects geocoded: {len(proj)} | listings: {len(df)}", flush=True)

    results = []
    results.append(evaluate(apply_variant(df, proj, "baseline", pids), "A: baseline", pids))
    results.append(evaluate(apply_variant(df, proj, "project_fill", pids), "B: project_fill (nominatim anchor)", pids))
    results.append(evaluate(apply_variant(df, proj, "project_override", pids), "C: project_override (nominatim anchor)", pids))
    results.append(evaluate(apply_variant(df, proj, "hybrid", pids, thresh_km=5.0), "D: hybrid >5km", pids))
    results.append(evaluate(apply_variant(df, proj, "hybrid", pids, thresh_km=3.0), "D2: hybrid >3km", pids))

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nSaved -> {OUT}", flush=True)


if __name__ == "__main__":
    main()
