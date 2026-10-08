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


def test_simulate_monotonic_on_market_presets():
    """Monotonisitas diuji pada jalur yang benar-benar dilalui pengguna.

    Assert lama "4BR >= 2BR pada LUAS YANG SAMA (120 m2)" DIHAPUS karena tidak
    didukung data. Di Jakarta Selatan 1BR median 60 m2 sedangkan 2BR median 94 m2:
    pada luas yang sama, jumlah kamar lebih sedikit menandakan unit yang lebih
    premium, dan model memang memprediksi demikian (R2 out-of-fold 0,83; bias di
    segmen JakSel 2BR 55-90 m2 hanya +8,5%).

    Yang dulu menyembunyikan fakta itu adalah loop max() di server: permintaan
    2BR 70 m2 dijawab dengan prediksi studio 70 m2 sehingga keluar Rp 28,25 jt,
    padahal median aktual segmennya Rp 17,0 jt (+64%). Lihat
    test_simulate_estimate_is_calibrated_to_market_median(), test level produk
    yang menangkap persis bug tersebut.
    """
    # 1. Menambah kamar pada luas TIPIKAL pasarnya selalu menaikkan estimasi.
    #    Ini jalur UX sebenarnya: UI menyinkronkan luas ke BEDROOM_PRESETS saat
    #    jumlah kamar diubah (simulator.js).
    previous = 0.0
    for beds, size in ((0, 28), (1, 45), (2, 70), (3, 120), (4, 200)):
        r = client.post("/api/simulate", json={
            "city": "Jakarta Selatan", "floor_size_m2": size, "bedrooms": beds
        }).json()
        assert r["fair_market_rent_idr"] > previous, (
            f"{beds}BR @ {size} m2 (Rp {r['fair_market_rent_idr']:,.0f}) tidak lebih mahal "
            f"dari konfigurasi sebelumnya (Rp {previous:,.0f})"
        )
        previous = r["fair_market_rent_idr"]

    # 2. Pada preset tipikal pasar (2BR 70 m2 vs 4BR 200 m2): 4BR jauh lebih mahal
    r2_preset = client.post("/api/simulate", json={"city": "Jakarta Selatan", "floor_size_m2": 70, "bedrooms": 2, "bathrooms": 1}).json()
    r4_preset = client.post("/api/simulate", json={"city": "Jakarta Selatan", "floor_size_m2": 200, "bedrooms": 4, "bathrooms": 3}).json()
    assert r4_preset["fair_market_rent_idr"] > r2_preset["fair_market_rent_idr"] * 1.5


def test_simulate_estimate_is_calibrated_to_market_median():
    """Estimasi simulator harus dekat dengan median harga pasar segmennya.

    Test level produk ini yang seharusnya menangkap bug max()-envelope: dulu
    estimasi default keluar Rp 28,25 jt sementara median aktual segmen
    JakSel 2BR 55-90 m2 adalah Rp 17,0 jt (+66%), dan median aktual itu ada DI
    LUAR rentang kepercayaan yang ditampilkan ke pengguna.
    """
    df_eval = pd.read_csv(os.path.join(BASE, "data", "processed", "jabodetabek_rental_evaluated.csv"))
    seg = df_eval[(df_eval.target_city == "Jakarta Selatan")
                  & (df_eval.bedrooms == 2)
                  & (df_eval.floor_size_m2.between(55, 90))]
    assert len(seg) >= 5, "Segmen pembanding terlalu kecil untuk test kalibrasi"
    median_actual = float(seg.price_monthly_idr.median())

    # Konfigurasi tanpa furnishing/amenitas: paling dekat ke "unit median" segmen.
    r = client.post("/api/simulate", json={
        "city": "Jakarta Selatan", "floor_size_m2": 70, "bedrooms": 2, "bathrooms": 1,
        "is_full_furnished": False, "has_pool": False
    }).json()
    ratio = r["fair_market_rent_idr"] / median_actual
    assert 0.75 <= ratio <= 1.35, (
        f"Estimasi Rp {r['fair_market_rent_idr']:,.0f} terlalu jauh dari median aktual "
        f"Rp {median_actual:,.0f} (rasio {ratio:.2f}) - curigai counterfactual substitution "
        f"atau pengali hardcoded yang menumpuk."
    )

    # Median aktual harus masuk rentang kepercayaan yang ditampilkan ke pengguna.
    assert r["ci_lower_idr"] <= median_actual <= r["ci_upper_idr"], (
        "Median harga aktual segmen berada di luar rentang kepercayaan yang ditampilkan"
    )


def test_simulate_reports_data_support():
    """Estimasi harus menyertakan seberapa kuat data nyata mendukungnya.

    Model pohon bisa mengekstrapolasi diam-diam ke kombinasi kamar/luas yang tidak
    ada di dataset; UI perlu angka pendukung supaya tidak menampilkan keyakinan palsu.
    """
    r = client.post("/api/simulate", json={"city": "Jakarta Selatan", "floor_size_m2": 70, "bedrooms": 2}).json()
    sup = r["data_support"]
    assert sup["support_level"] in ("strong", "limited", "extrapolated")
    assert sup["scope"] in ("city", "national")
    assert sup["comparables_matched"] >= 1, "Harus ada listing pembanding untuk konfigurasi umum"
    assert sup["support_level"] in ("strong", "limited"), "Konfigurasi umum harus punya dukungan data nyata"
    assert sup["median_comparable_rent_idr"] and sup["median_comparable_rent_idr"] > 0
    assert sup["inside_typical_size_range"] is True, "70 m2 adalah luas normal untuk 2BR"


def test_simulate_flags_extrapolated_estimates():
    """Konfigurasi yang tidak ada di data harus ditandai, bukan ditampilkan seolah yakin.

    Contoh: 5BR di Jakarta Selatan. Di dataset 5BR = 0 unit di kota tsb, fallback
    ke national pun 0 comparables dalam ±25%. Sebelumnya UI menampilkan
    "median Rp 0.0 jt" karena field median bernilai null.
    """
    r = client.post("/api/simulate", json={"city": "Jakarta Selatan", "floor_size_m2": 300, "bedrooms": 5}).json()
    sup = r["data_support"]
    assert sup["support_level"] == "extrapolated", "5BR 300 m2 JakSel tidak punya pembanding di data"
    assert sup["comparables_matched"] == 0
    assert sup["median_comparable_rent_idr"] is None, (
        "median pembanding harus null (bukan 0) supaya UI tidak menampilkan angka palsu"
    )
    # scope fallback ke national karena 5BR JakSel = 0
    assert sup["scope"] == "national"


def test_simulate_bathrooms_impact_price():
    """Jumlah kamar mandi tambahan (ensuite / private bath) menambah nilai sewa secara proporsional."""
    b1 = client.post("/api/simulate", json={"city": "Jakarta Selatan", "floor_size_m2": 70, "bedrooms": 2, "bathrooms": 1}).json()
    b2 = client.post("/api/simulate", json={"city": "Jakarta Selatan", "floor_size_m2": 70, "bedrooms": 2, "bathrooms": 2}).json()
    b3 = client.post("/api/simulate", json={"city": "Jakarta Selatan", "floor_size_m2": 70, "bedrooms": 2, "bathrooms": 3}).json()
    assert b2["fair_market_rent_idr"] > b1["fair_market_rent_idr"]
    assert b3["fair_market_rent_idr"] > b2["fair_market_rent_idr"]


def test_simulate_furnishing_condition_tiers():
    """Tingkat kelengkapan perabot: Full Furnished > Semi Furnished > Unfurnished."""
    full = client.post("/api/simulate", json={"city": "Jakarta Selatan", "floor_size_m2": 70, "bedrooms": 2, "is_full_furnished": True, "is_semi_furnished": False}).json()
    semi = client.post("/api/simulate", json={"city": "Jakarta Selatan", "floor_size_m2": 70, "bedrooms": 2, "is_full_furnished": False, "is_semi_furnished": True}).json()
    un = client.post("/api/simulate", json={"city": "Jakarta Selatan", "floor_size_m2": 70, "bedrooms": 2, "is_full_furnished": False, "is_semi_furnished": False}).json()
    assert full["fair_market_rent_idr"] > semi["fair_market_rent_idr"]
    assert semi["fair_market_rent_idr"] > un["fair_market_rent_idr"]


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
