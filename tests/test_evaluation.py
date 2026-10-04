"""Test dedup konten dan evaluasi out-of-fold (python -m pytest tests -q)."""
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from transformation import drop_content_duplicates
from market_intelligence import regression_metrics, compute_deal_scores, out_of_fold_log_predictions
from sklearn.model_selection import KFold


def _listings():
    return pd.DataFrame({
        "price_monthly_idr": [5e6, 5e6, 5e6, 8e6],
        "floor_size_m2": [36.0, 36.0, 36.0, 36.0],
        "bedrooms": [1, 1, 2, 1],
        "bathrooms": [1, 1, 1, 1],
        "display_location": ["Menteng, Jakarta Pusat"] * 4,
        "url": list("abcd"),
    })


def test_content_dedup_drops_only_true_twins():
    out, n = drop_content_duplicates(_listings())
    assert n == 1                      # baris 0 & 1 kembar; baris 2 beda kamar; baris 3 beda harga
    assert list(out["url"]) == ["a", "c", "d"]   # yang pertama dipertahankan


def test_regression_metrics_perfect_and_biased():
    a = np.array([4e6, 6e6, 10e6])
    assert regression_metrics(a, a)["mape_pct"] == 0
    m = regression_metrics(a, a * 1.1)
    assert abs(m["mape_pct"] - 10.0) < 1e-6 and abs(m["median_ape_pct"] - 10.0) < 1e-6


def test_deal_score_uses_log_scale_and_flags_cheap_unit():
    df = pd.DataFrame({"price_monthly_idr": [3e6, 3e6, 3e6, 3e6, 1.5e6]})
    out = compute_deal_scores(df, np.array([3e6, 3e6, 3e6, 3e6, 3e6]))
    assert out.loc[4, "deal_score_z"] < -0.75
    assert out.loc[4, "discount_pct"] == 50.0
    assert out.loc[0, "deal_classification"] == "Fair Market Price"


def test_oof_predictions_never_use_own_row():
    # target murni acak: model yang jujur TIDAK boleh menghafalnya (R2 OOF ~ <= 0), in-sample bisa tinggi
    rng = np.random.default_rng(0)
    n = 120
    X = pd.DataFrame({"f1": rng.normal(size=n), "f2": rng.normal(size=n)})
    y = pd.Series(rng.normal(15, 0.3, size=n))
    df = pd.DataFrame({"target_city": ["A"] * n, "price_per_m2_idr": np.exp(y) / 40, "floor_size_m2": 40.0})
    splits = [list(KFold(5, shuffle=True, random_state=1).split(X))]
    oof = out_of_fold_log_predictions(df, X, y, splits)["gb"][0]
    from sklearn.metrics import r2_score
    assert r2_score(y, oof) < 0.15
