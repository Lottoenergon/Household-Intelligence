"""
hedonic_ols.py
Lapisan hedonik interpretable: OLS pada log-sewa bulanan.

Gradient Boosting di market_intelligence.py akurat tapi tidak bisa menjawab
"berapa premi untuk satu fitur". Modul ini menjawabnya: koefisien OLS pada
ln(harga) dikonversi ke implicit price (% perubahan harga, ceteris paribus)
dengan standard error robust (HC1) dan CI 95%.

Sengaja tanpa statsmodels: cukup numpy, supaya tidak menambah dependency.
"""

import json
import os
from typing import Dict, List, Any

import numpy as np
import pandas as pd

Z95 = 1.959963984540054
CONTINUOUS = {"log_floor_size", "distance_to_cbd_km", "distance_to_transit_km"}


def _design(df: pd.DataFrame, feature_cols: List[str]) -> pd.DataFrame:
    """Matriks desain dengan konstanta; kolom kota sudah dummy (drop_first)."""
    X = df[feature_cols].astype(float).copy()
    X.insert(0, "const", 1.0)
    return X


def fit_ols_hc1(X: np.ndarray, y: np.ndarray) -> Dict[str, np.ndarray]:
    """OLS dengan standard error HC1 (robust terhadap heteroskedastisitas)."""
    n, k = X.shape
    XtX_inv = np.linalg.pinv(X.T @ X)
    beta = XtX_inv @ X.T @ y
    resid = y - X @ beta
    meat = (X * (resid ** 2)[:, None]).T @ X
    cov = (n / (n - k)) * XtX_inv @ meat @ XtX_inv
    return {"beta": beta, "se": np.sqrt(np.clip(np.diag(cov), 0, None)), "resid": resid}


def oof_r2_ols(X: np.ndarray, y: np.ndarray, n_splits: int = 5, seed: int = 42) -> float:
    """R2 out-of-fold (skala log) untuk menilai apakah OLS layak dibanding model GB."""
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(y))
    folds = np.array_split(idx, n_splits)
    pred = np.zeros(len(y))
    for te in folds:
        tr = np.setdiff1d(idx, te)
        b = np.linalg.pinv(X[tr].T @ X[tr]) @ X[tr].T @ y[tr]
        pred[te] = X[te] @ b
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    return 1.0 - ss_res / ss_tot


def implicit_prices(df: pd.DataFrame, feature_cols: List[str]) -> Dict[str, Any]:
    """Implicit price per fitur dalam persen, dengan CI 95%.

    Dummy (biner): efek = exp(b) - 1 terhadap baseline.
    Kontinu (log luas): efek per +10% luas = exp(b * ln 1.1) - 1.
    Jarak: efek per +1 km.
    """
    X = _design(df, feature_cols)
    y = np.log(df["price_monthly_idr"].astype(float).values)
    fit = fit_ols_hc1(X.values, y)
    beta, se = fit["beta"], fit["se"]

    rows = []
    for i, name in enumerate(X.columns):
        if name == "const":
            continue
        b, s = beta[i], se[i]
        lo, hi = b - Z95 * s, b + Z95 * s
        if name == "log_floor_size":
            scale, unit = np.log(1.1), "per +10% luas"
        elif name.startswith("distance_"):
            scale, unit = 1.0, "per +1 km"
        else:
            scale, unit = 1.0, "vs baseline"
        f = lambda v: round(float((np.exp(v * scale) - 1) * 100), 2)
        rows.append({
            "feature": name,
            "unit": unit,
            "effect_pct": f(b),
            "ci95_pct": [f(lo), f(hi)],
            "significant": bool(np.sign(lo) == np.sign(hi)),
        })

    yhat = X.values @ beta
    ss_res = float(np.sum((y - yhat) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    return {
        "model_type": "OLS on ln(monthly rent), HC1 robust SE",
        "n": int(len(y)),
        "r2_in_sample_log": round(1 - ss_res / ss_tot, 4),
        "r2_oof_log": round(oof_r2_ols(X.values, y), 4),
        "effects": rows,
    }


def run(base_dir: str) -> Dict[str, Any]:
    """Baca dataset bersih, pakai fitur yang SAMA dengan training GB, tulis JSON."""
    import sys
    sys.path.insert(0, os.path.join(base_dir, "src"))
    from market_intelligence import build_hedonic_features

    clean = os.path.join(base_dir, "data", "processed", "jabodetabek_rental_cleaned.csv")
    out = os.path.join(base_dir, "data", "processed", "hedonic_implicit_prices.json")
    df = pd.read_csv(clean)
    X, _, cols = build_hedonic_features(df)
    df_feat = pd.concat([df[["price_monthly_idr"]], X], axis=1)
    result = implicit_prices(df_feat, cols)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    return result


if __name__ == "__main__":
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    res = run(base)
    print(f"n={res['n']} R2 in-sample={res['r2_in_sample_log']} OOF={res['r2_oof_log']}")
    for e in res["effects"]:
        print(f"{e['feature']:<26} {e['effect_pct']:>8.2f}%  CI {e['ci95_pct']}  sig={e['significant']}")
