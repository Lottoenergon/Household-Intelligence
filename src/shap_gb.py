"""SHAP explanations untuk model GB hedonik (models/hedonic_gb.joblib).

Read-only terhadap pipeline: tidak melatih ulang, tidak mengubah artefak GB.
Output: data/processed/shap_gb_summary.json
  - global: mean(|SHAP|) per fitur pada skala log-rent (ln IDR)
  - effect_pct: perkiraan dampak % terhadap rent = exp(mean SHAP sign-weighted) - 1 (ringkas)
  - local: contoh penjelasan per listing (top 3 fitur)
"""
import json
import os

import joblib
import numpy as np
import pandas as pd
import shap

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "hedonic_gb.joblib")
DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "jabodetabek_rental_evaluated.csv")
OUT_PATH = os.path.join(BASE_DIR, "data", "processed", "shap_gb_summary.json")


def run(sample_n: int = 300, local_n: int = 5, seed: int = 42) -> dict:
    art = joblib.load(MODEL_PATH)
    model, cols = art["model"], art["feature_columns"]

    df = pd.read_csv(DATA_PATH)
    X = build_matrix(df, cols)
    sample = X.sample(min(sample_n, len(X)), random_state=seed)

    explainer = shap.TreeExplainer(model)
    sv = explainer.shap_values(sample)  # shape (n, p), units: ln(IDR)
    base_ln = float(np.asarray(explainer.expected_value).ravel()[0])

    mean_abs = np.abs(sv).mean(axis=0)
    total = mean_abs.sum()
    global_imp = sorted(
        [
            {
                "feature": c,
                "mean_abs_shap_log": round(float(m), 4),
                "share_pct": round(float(m / total * 100), 2),
            }
            for c, m in zip(cols, mean_abs)
        ],
        key=lambda d: d["mean_abs_shap_log"],
        reverse=True,
    )

    local = []
    for i in range(min(local_n, len(sample))):
        idx = sample.index[i]
        contrib = sorted(zip(cols, sv[i]), key=lambda t: abs(t[1]), reverse=True)[:3]
        local.append(
            {
                "listing_id": str(df.loc[idx, "listing_id"]),
                "base_value_idr": round(float(np.exp(base_ln)), 0),
                "top_contributions": [
                    {"feature": c, "shap_log": round(float(v), 4)} for c, v in contrib
                ],
            }
        )

    out = {
        "model": "GradientBoostingRegressor (hedonic_gb.joblib)",
        "sample_n": int(len(sample)),
        "units": "SHAP values are on ln(IDR) scale; share_pct = share of total |SHAP|",
        "base_value_ln": round(base_ln, 4),
        "global_importance": global_imp,
        "local_examples": local,
    }
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    return out


def build_matrix(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    """Rekonstruksi matriks fitur persis seperti build_features() di market_intelligence.py."""
    X = pd.DataFrame(index=df.index)
    X["log_floor_size"] = np.log(df["floor_size_m2"].astype(float))
    X["bedrooms"] = df["bedrooms"].astype(float)
    X["bathrooms"] = df["bathrooms"].astype(float)
    X["distance_to_cbd_km"] = df["distance_to_cbd_km"].astype(float)
    X["distance_to_transit_km"] = df["distance_to_transit_km"].astype(float)
    amenity_cols = [
        "is_full_furnished", "is_semi_furnished", "has_ac", "has_wifi",
        "has_water_heater", "has_pool", "has_gym", "near_transit",
        "has_balcony", "has_kitchen", "has_parking",
    ]
    for c in amenity_cols:
        X[c] = df[c].astype(int)
    dummies = pd.get_dummies(df["target_city"], prefix="city", drop_first=True)
    for c in dummies.columns:
        X[c] = dummies[c].astype(int)
    missing = [c for c in cols if c not in X.columns]
    if missing:
        raise ValueError(f"Fitur tidak terbentuk: {missing}")
    return X[cols]


if __name__ == "__main__":
    res = run()
    for g in res["global_importance"][:10]:
        print(f'{g["feature"]:30s} {g["mean_abs_shap_log"]:.4f}  {g["share_pct"]:6.2f}%')
    print("wrote", OUT_PATH)
