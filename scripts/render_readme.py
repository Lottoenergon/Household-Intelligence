"""Render README.md dari README.template.md. Semua angka diambil dari artefak pipeline
(model_evaluation_metrics.json, market_summary.json), tidak ada angka yang diketik manual.

Pakai:  python scripts/render_readme.py          -> tulis README.md
        python scripts/render_readme.py --check  -> exit 1 jika README.md basi (tidak sama dengan hasil render)
"""
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(BASE, "data", "processed")

FEATURE_LABELS = {"log_floor_size": "Floor area (log m²)", "distance_to_cbd_km": "Distance to CBD",
                  "distance_to_transit_km": "Distance to nearest transit hub", "bedrooms": "Bedrooms",
                  "bathrooms": "Bathrooms", "is_full_furnished": "Full furnished flag"}


def _label(f: str) -> str:
    return FEATURE_LABELS.get(f, f.replace("city_", "City: "))


def build_context() -> dict:
    m = json.load(open(os.path.join(PROC, "model_evaluation_metrics.json"), encoding="utf-8"))
    s = json.load(open(os.path.join(PROC, "market_summary.json"), encoding="utf-8"))
    a = s["audit"]
    k, g = m["evaluation"]["kfold_5x3"], m["evaluation"]["group_kfold_subdistrict"]
    iv, d = m["prediction_interval"], s["deals"]

    def row(name, e):
        return f"| {name} | {e['r2']:.3f} | Rp {e['mae_idr']/1e6:.2f}M | {e['mape_pct']:.1f}% | {e['median_ape_pct']:.1f}% |"

    eval_rows = []
    for title, block in (("Known areas (5-fold CV x3 repeats)", k), ("Unseen subdistricts (GroupKFold)", g)):
        eval_rows.append(f"| **{title}** | | | | |")
        for key, name in (("naive", "Baseline: city median price/m² x size"), ("ridge", "Ridge regression"),
                          ("gb", "Gradient Boosting (final model)")):
            eval_rows.append(row(name, block[key]))
    feat_rows = [f"| {i+1} | {_label(f['feature'])} | {f['importance']*100:.1f}% |" for i, f in enumerate(m["feature_importances"][:6])]
    city_rows = [f"| {c['target_city']} | {int(c['n'])} | Rp {c['median_price_per_m2_idr']/1000:.0f}k | Rp {c['median_rent_idr']/1e6:.1f}M | "
                 f"{s['geo']['imputed_share_pct_by_city'].get(c['target_city'], 0):.0f}% |" for c in s["by_city"]]

    return {
        "n_raw": a["raw_records"], "n_url_dups": a["raw_records"] - a["after_url_dedup"],
        "n_price_removed": a["after_url_dedup"] - a["after_price_validation"],
        "n_content_dups": a["content_duplicates_removed"], "n_final": a["final_records"],
        "n_subdistricts": m["n_subdistricts"], "n_cities": s["n_cities"],
        "n_floor_imputed": a["floor_size_missing_imputed"],
        "r2": f"{k['gb']['r2']:.3f}", "mae_m": f"{k['gb']['mae_idr']/1e6:.2f}", "mape": f"{k['gb']['mape_pct']:.1f}",
        "medape": f"{k['gb']['median_ape_pct']:.1f}", "naive_r2": f"{k['naive']['r2']:.3f}",
        "group_gb_r2": f"{g['gb']['r2']:.3f}", "group_naive_r2": f"{g['naive']['r2']:.3f}",
        "train_r2": f"{m['train_in_sample_r2_DIAGNOSTIC_ONLY']:.3f}",
        "iv_level": int(iv["level"] * 100), "iv_lo": f"{(iv['lower_factor']-1)*100:.0f}", "iv_hi": f"+{(iv['upper_factor']-1)*100:.0f}",
        "below_n": d["below_estimate_total"], "below_pct": d["below_estimate_share_pct"],
        "above_n": d["above_estimate_total"], "above_pct": d["above_estimate_share_pct"],
        "median_discount": d["median_discount_pct_of_flagged"],
        "tier_premium": s["tier1_vs_tier3_premium_pct"], "furn_raw": s["furnishing_premium_raw_pct"],
        "furn_adj": s["furnishing_premium_adjusted_pct"], "furnished_share": s["furnished_share_pct"],
        "geo_imputed_pct": s["geo"]["imputed_share_pct"],
        "tangsel_imputed_pct": f"{s['geo']['imputed_share_pct_by_city'].get('Tangerang Selatan', 0):.0f}",
        "median_rent_m": f"{s['median_rent_idr']/1e6:.1f}", "median_ppm2_k": f"{s['median_price_per_m2_idr']/1000:.0f}",
        "eval_table": "\n".join(eval_rows), "feature_table": "\n".join(feat_rows), "city_table": "\n".join(city_rows),
    }


def render() -> str:
    tpl = open(os.path.join(BASE, "README.template.md"), encoding="utf-8").read()
    ctx = build_context()
    out = re.sub(r"\{\{(\w+)\}\}", lambda mo: str(ctx[mo.group(1)]), tpl)  # KeyError jika placeholder tak dikenal
    assert "{{" not in out
    return out


if __name__ == "__main__":
    text = render()
    path = os.path.join(BASE, "README.md")
    if "--check" in sys.argv:
        sys.exit(0 if os.path.exists(path) and open(path, encoding="utf-8").read() == text else 1)
    open(path, "w", encoding="utf-8").write(text)
    print("README.md rendered from pipeline artifacts.")
