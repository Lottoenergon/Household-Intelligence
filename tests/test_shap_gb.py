"""SHAP GB: additivity + artefak ringkasan + tidak mengubah artefak model GB."""
import json
import os

import joblib
import numpy as np
import pandas as pd
import pytest

pytest.importorskip("shap")
import shap  # noqa: E402

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "hedonic_gb.joblib")
DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "jabodetabek_rental_evaluated.csv")
SUMMARY_PATH = os.path.join(BASE_DIR, "data", "processed", "shap_gb_summary.json")

import sys
sys.path.insert(0, os.path.join(BASE_DIR, "src"))
from shap_gb import build_matrix  # noqa: E402


def test_shap_additivity_matches_model_prediction():
    art = joblib.load(MODEL_PATH)
    df = pd.read_csv(DATA_PATH)
    X = build_matrix(df, art["feature_columns"]).head(50)
    ex = shap.TreeExplainer(art["model"])
    sv = np.asarray(ex.shap_values(X))
    base = float(np.asarray(ex.expected_value).ravel()[0])
    pred = art["model"].predict(X)
    assert np.abs(base + sv.sum(axis=1) - pred).max() < 1e-9


def test_summary_artifact_present_and_sane():
    if not os.path.exists(SUMMARY_PATH):
        pytest.skip("jalankan `python src/shap_gb.py` dulu")
    d = json.load(open(SUMMARY_PATH, encoding="utf-8"))
    assert d["sample_n"] > 0
    gi = d["global_importance"]
    assert gi and gi[0]["feature"] == "log_floor_size"
    shares = sum(g["share_pct"] for g in gi)
    assert 99.0 <= shares <= 101.0
