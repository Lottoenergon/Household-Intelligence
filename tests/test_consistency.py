"""Pastikan API, UI, dan README selalu cocok dengan output pipeline (anti angka basi / hardcode).
Jalankan setelah `python run_pipeline.py`:  python -m pytest tests -q
"""
import json
import os
import re
import sys

import pandas as pd
import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "src"))
sys.path.insert(0, os.path.join(BASE, "scripts"))

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient  # noqa: E402
from backend import server  # noqa: E402
import render_readme  # noqa: E402
from market_intelligence import build_hedonic_features  # noqa: E402

client = TestClient(server.app)
METRICS = json.load(open(os.path.join(BASE, "data", "processed", "model_evaluation_metrics.json"), encoding="utf-8"))


def test_telemetry_matches_metrics_file():
    t = client.get("/api/telemetry").json()
    gb = METRICS["evaluation"]["kfold_5x3"]["gb"]
    assert t["model"]["r2"] == gb["r2"] and t["model"]["mape_pct"] == gb["mape_pct"]
    assert t["audited_units"] == METRICS["sample_size"]


def test_readme_is_not_stale_and_contains_oof_r2():
    text = render_readme.render()
    assert f"{METRICS['evaluation']['kfold_5x3']['gb']['r2']:.3f}" in text
    assert open(os.path.join(BASE, "README.md"), encoding="utf-8").read() == text, "README basi: jalankan run_pipeline.py"


def test_frontend_has_no_known_stale_claims():
    html = open(os.path.join(BASE, "frontend", "index.html"), encoding="utf-8").read()
    for stale in ("26.8%", "95.9%", "83.5%", "13.7% MAPE", "1.4 Years (17 Months)", "787 UNIT"):
        assert stale not in html


def test_served_features_match_training_features():
    df = pd.read_csv(os.path.join(BASE, "data", "processed", "jabodetabek_rental_cleaned.csv"))
    X, _, _ = build_hedonic_features(df)
    assert list(X.columns) == server.FEATURE_COLUMNS      # cegah train/serve skew


def test_simulate_uses_model_bigger_unit_costs_more_and_range_is_ordered():
    small = client.post("/api/simulate", json={"city": "Jakarta Selatan", "floor_size_m2": 30}).json()
    big = client.post("/api/simulate", json={"city": "Jakarta Selatan", "floor_size_m2": 90}).json()
    assert big["fair_market_rent_idr"] > small["fair_market_rent_idr"]
    for r in (small, big):
        assert r["ci_lower_idr"] < r["fair_market_rent_idr"] < r["ci_upper_idr"]
        assert r["interval_level_pct"] == 80


def test_simulate_monotonic_bedrooms_and_realistic_presets():
    """Memastikan unit 4BR tidak pernah lebih murah dari 2BR baik pada luas tetap maupun tipikal pasar."""
    # 1. Pada luas tetap (misal 120 m2) di kota yang sama: 4BR >= 2BR
    r2_same = client.post("/api/simulate", json={"city": "Jakarta Selatan", "floor_size_m2": 120, "bedrooms": 2, "bathrooms": 2}).json()
    r4_same = client.post("/api/simulate", json={"city": "Jakarta Selatan", "floor_size_m2": 120, "bedrooms": 4, "bathrooms": 3}).json()
    assert r4_same["fair_market_rent_idr"] >= r2_same["fair_market_rent_idr"]

    # 2. Pada preset tipikal pasar (2BR 70 m2 vs 4BR 200 m2): 4BR jauh lebih mahal
    r2_preset = client.post("/api/simulate", json={"city": "Jakarta Selatan", "floor_size_m2": 70, "bedrooms": 2, "bathrooms": 1}).json()
    r4_preset = client.post("/api/simulate", json={"city": "Jakarta Selatan", "floor_size_m2": 200, "bedrooms": 4, "bathrooms": 3}).json()
    assert r4_preset["fair_market_rent_idr"] > r2_preset["fair_market_rent_idr"] * 1.5


def test_simulate_monotonic_amenities_never_decrease_rent():
    """Fasilitas fisik (AC, Kitchen, Pool, Gym, Balcony, Near Transit) tidak boleh menurunkan estimasi sewa."""
    base_payload = {
        "city": "Jakarta Selatan",
        "subdistrict": "Kemang",
        "floor_size_m2": 70,
        "bedrooms": 2,
        "bathrooms": 1,
        "has_ac": False,
        "has_kitchen": False,
        "has_pool": False,
        "has_gym": False,
        "has_balcony": False,
        "near_transit": False
    }
    base_rent = client.post("/api/simulate", json=base_payload).json()["fair_market_rent_idr"]

    for amenity in ["has_ac", "has_kitchen", "has_pool", "has_gym", "has_balcony", "near_transit"]:
        amenity_payload = dict(base_payload)
        amenity_payload[amenity] = True
        amenity_rent = client.post("/api/simulate", json=amenity_payload).json()["fair_market_rent_idr"]
        assert amenity_rent >= base_rent, f"{amenity} seharusnya menambah atau mempertahankan nilai sewa"


def test_simulate_subdistrict_micromarket_sanity():
    """Kawasan prime di dalam satu kota secara objektif memiliki valuasi lebih tinggi dibanding kawasan industri mass-market."""
    pekayon = client.post("/api/simulate", json={"city": "Bekasi", "subdistrict": "Pekayon", "floor_size_m2": 60}).json()
    cikarang = client.post("/api/simulate", json={"city": "Bekasi", "subdistrict": "Cikarang", "floor_size_m2": 60}).json()
    assert pekayon["fair_market_rent_idr"] > cikarang["fair_market_rent_idr"]


def test_simulate_rejects_unknown_city_and_out_of_range_size():
    assert client.post("/api/simulate", json={"city": "Surabaya"}).status_code == 400
    assert client.post("/api/simulate", json={"floor_size_m2": 900}).status_code == 400


def test_fitout_cost_is_a_parameter_not_a_constant():
    a = client.post("/api/simulate", json={"city": "Jakarta Selatan", "fitout_cost_per_m2_idr": 600_000}).json()
    b = client.post("/api/simulate", json={"city": "Jakarta Selatan", "fitout_cost_per_m2_idr": 1_200_000}).json()
    assert b["furnishing_analysis"]["estimated_fitout_cost_idr"] == 2 * a["furnishing_analysis"]["estimated_fitout_cost_idr"]


def test_sql_deal_view_uses_same_threshold_as_summary():
    import sqlite3
    summary = json.load(open(os.path.join(BASE, "data", "processed", "market_summary.json"), encoding="utf-8"))
    conn = sqlite3.connect(os.path.join(BASE, "data", "processed", "rental_intelligence.db"))
    n = conn.execute("SELECT COUNT(*) FROM view_top_undervalued_deals").fetchone()[0]
    conn.close()
    assert n == summary["deals"]["below_estimate_total"]
