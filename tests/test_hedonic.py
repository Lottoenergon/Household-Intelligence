"""Test lapisan hedonik interpretable (OLS log-rent, HC1)."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from hedonic_ols import fit_ols_hc1, implicit_prices, _design

BASE = os.path.join(os.path.dirname(__file__), "..")


def _synthetic():
    """Data sintetis dengan harga yang diketahui: full_furnished +20%, CBD -2%/km."""
    rng = np.random.default_rng(7)
    n = 400
    df = pd.DataFrame({
        "price_monthly_idr": np.zeros(n),
        "log_floor_size": np.log(rng.uniform(25, 120, n)),
        "distance_to_cbd_km": rng.uniform(1, 30, n),
        "distance_to_transit_km": rng.uniform(0.1, 5, n),
        "bedrooms": rng.integers(1, 4, n),
        "bathrooms": np.ones(n),
        "is_full_furnished": rng.integers(0, 2, n),
        "is_semi_furnished": np.zeros(n, dtype=int),
        "has_ac": np.ones(n, dtype=int),
        "has_wifi": np.zeros(n, dtype=int),
        "has_water_heater": np.zeros(n, dtype=int),
        "has_pool": np.zeros(n, dtype=int),
        "has_gym": np.zeros(n, dtype=int),
        "near_transit": np.zeros(n, dtype=int),
        "has_balcony": np.zeros(n, dtype=int),
        "has_kitchen": np.zeros(n, dtype=int),
        "has_parking": np.zeros(n, dtype=int),
        "city_A": np.zeros(n, dtype=int),
    })
    logp = (15.0 + 0.9 * df["log_floor_size"] - 0.02 * df["distance_to_cbd_km"]
            + np.log(1.20) * df["is_full_furnished"] + rng.normal(0, 0.03, n))
    df["price_monthly_idr"] = np.exp(logp)
    cols = [c for c in df.columns if c != "price_monthly_idr"]
    return df, cols


def test_ols_recovers_known_effects():
    df, cols = _synthetic()
    res = implicit_prices(df, cols)
    eff = {e["feature"]: e for e in res["effects"]}
    # furnishing +20% -> toleransi ±4pp (noise kecil, n=400)
    assert abs(eff["is_full_furnished"]["effect_pct"] - 20.0) < 4.0
    # CBD -2%/km -> exp(-0.02)-1 ≈ -1.98%
    assert abs(eff["distance_to_cbd_km"]["effect_pct"] - (-1.98)) < 1.0
    # dua-duanya signifikan
    assert eff["is_full_furnished"]["significant"] and eff["distance_to_cbd_km"]["significant"]


def test_hc1_se_matches_closed_form():
    """SE HC1 harus sama dengan rumus sandwich yang dihitung manual di test."""
    rng = np.random.default_rng(3)
    n, k = 60, 4
    X = np.column_stack([np.ones(n), rng.normal(size=(n, k - 1))])
    y = X @ np.array([1.0, 0.5, -0.3, 0.2]) + rng.normal(0, 0.5, n)
    fit = fit_ols_hc1(X, y)
    beta_hat = np.linalg.pinv(X.T @ X) @ X.T @ y
    r = y - X @ beta_hat
    XtXi = np.linalg.pinv(X.T @ X)
    cov = (n / (n - k)) * XtXi @ ((X * r[:, None] ** 2).T @ X) @ XtXi
    np.testing.assert_allclose(fit["se"], np.sqrt(np.diag(cov)), rtol=1e-10)
    np.testing.assert_allclose(fit["beta"], beta_hat, rtol=1e-10)


def test_hedonic_artifact_exists_and_has_ci():
    p = os.path.join(BASE, "data", "processed", "hedonic_implicit_prices.json")
    assert os.path.exists(p), "pipeline belum menulis hedonic_implicit_prices.json"
    res = json.load(open(p, encoding="utf-8"))
    cleaned = os.path.join(BASE, "data", "processed", "jabodetabek_rental_cleaned.csv")
    import pandas as pd
    n_clean = len(pd.read_csv(cleaned))
    assert res["n"] == n_clean and len(res["effects"]) > 10
    for e in res["effects"]:
        assert e["ci95_pct"][0] <= e["effect_pct"] <= e["ci95_pct"][1]
    assert "r2_oof_log" in res


def test_ols_is_honest_about_fit():
    """OLS linear pasti kalah dari GB non-linear — kalau OOF OLS > GB, ada yang salah."""
    p = os.path.join(BASE, "data", "processed", "hedonic_implicit_prices.json")
    res = json.load(open(p, encoding="utf-8"))
    metrics = json.load(open(os.path.join(BASE, "data", "processed",
                                          "model_evaluation_metrics.json"), encoding="utf-8"))
    gb_r2_log = metrics["evaluation"]["kfold_5x3"]["gb"]["r2_log"]
    assert res["r2_oof_log"] <= gb_r2_log + 0.01
