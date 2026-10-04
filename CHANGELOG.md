# Changelog

All notable changes to this project. The v0.3 work was a self-audit: I re-checked my own claims against the data, found problems, and fixed them. The problems are listed on purpose.

## [0.3.0] - 2026-10-04: audit and fixes (previous version: v0.2-alpha)

### Step 1: geo cleaning

**Problems found**
- 13 listings had longitude copied from latitude (for example -6.23168, -6.23168), producing distances of about 12,460 km to the CBD.
- 56 listings had no coordinates and were silently placed at the CBD point (distance 0 km). 51 of them were in South Tangerang, so BSD showed a median distance of 0 km.
- Both errors fed the distance features and the distance-decay finding.

**Changes**
- Coordinates validated against a Jabodetabek bounding box (rejects the copied-longitude case).
- Missing or invalid coordinates are imputed from the subdistrict median of valid coordinates (minimum 2 listings), then the city median. The CBD is never used as a fallback; unfixable rows stay NaN.
- New columns `geo_source` and `geo_is_imputed`.
- 6 tests, including "unfixable rows stay NaN, not invented".

**Effect:** zero rows with distance 0 km or above 100 km. The core-vs-outer-ring price premium stayed in the same range (61.5% -> 60.4% at that step; the definition later changed to the median, giving +63.0%). South Tangerang is **64% imputed**, so distances there are approximate. This is now disclosed in the README.

### Step 2: honest evaluation

**Problems found**
- R2 0.959, MAE Rp 1.11M and MAPE 13.7% were computed **in-sample** (the model was scored on the rows it was trained on).
- Deal residuals and z-scores were also in-sample, so they were shrunk by overfitting.
- No baseline, so R2 0.83 had no reference point.
- About 65 listings were cross-broker duplicates (same price, size, bedrooms, location) that URL de-duplication missed and that can leak across CV folds.
- Residuals were measured in Rupiah, so luxury units dominated the standard deviation and cheap units were rarely flagged.

**Changes**
- Out-of-fold evaluation with two schemes: repeated 5-fold CV (3 repeats), and GroupKFold by subdistrict to test unseen areas.
- Added a naive baseline (city median rent per m2 x size) and Ridge for comparison.
- Content-based de-duplication (59 rows removed); data now 800 raw -> 728 analysed.
- Deal score now uses the **log residual**; "fair rent" per listing is its out-of-fold prediction.
- In-sample R2 is stored only under the key `train_in_sample_r2_DIAGNOSTIC_ONLY`.
- 4 tests (dedup, metrics, deal score, out-of-fold predictions cannot memorise noise).

**Results (out-of-fold)**

| | Claimed before | Honest |
|---|---|---|
| R2 | 0.959 (in-sample) | 0.831 |
| MAE | Rp 1.11M | Rp 2.10M |
| MAPE | 13.7% | 25.4% (median APE 17.7%) |
| Listings flagged below estimate | 39 (README) / 60 (CSV) | 133 (18.3%), with 126 flagged above |

- The model beats the naive baseline (R2 0.737), but not by a huge margin.
- On subdistricts the model has never seen: Gradient Boosting 0.747, Ridge 0.745, baseline 0.710. Much of its skill comes from recognising the area.
- With typical error around 18-25%, "below estimate" listings are candidates to verify, not confirmed bargains.

### Step 3: single source of truth (README, UI and API vs. the model)

**Problems found**
- `/api/simulate` did not use the trained model. It multiplied a city median by hand-written constants (furnished x1.268, AC x1.08, pool x1.05, ...) and a fixed +/-10% band.
- Dashboard and server hard-coded model numbers ("R2 95.9%", "83.5%", "MAPE 13.7%", "787 units", "+26.8%") that did not match the pipeline output.
- README figures contradicted the project's own files: 39 "undervalued" deals in the README vs 60 in the CSV; feature importances (floor area 42.1%, distance 28.4%) vs the metrics JSON (floor area 67.4%); furnishing premium +26.8% vs about +12% in the raw medians.
- The SQL view `view_top_undervalued_deals` used z <= -1.0 while the README and API used z <= -0.75.
- The dashboard's fit-out payback demo showed "1.4 years", a number produced by the invented multipliers.

**Changes**
- The pipeline saves the final model (`models/hedonic_gb.joblib`); `/api/simulate` loads that same model. Feature construction is shared with training, and a test guards against train/serve skew.
- The simulator returns an **empirical 80% range** from out-of-fold residuals (about -32% / +42%), replaces the fixed +/-10%, and rejects unknown cities and sizes outside 15-350 m2.
- The fit-out cost per m2 is now an explicit request parameter, labelled as a user assumption, not data.
- The pipeline writes `model_evaluation_metrics.json`, `market_summary.json` and `pipeline_audit.json`. API telemetry, the dashboard and the README read from them.
- `README.md` is rendered by `scripts/render_readme.py` from `README.template.md`. Edit the template, not the README.
- README rewritten: removed unsupported wording ("production-grade", "SaaS", "sub-10ms", "verified"), added results with baselines, and a limitations section.
- SQL deal view aligned to z <= -0.75.
- 8 consistency tests (API vs metrics file, README not stale, no stale claims in `index.html`, feature columns match between training and serving, SQL vs summary, simulator sanity).

**Effect:** with the model's own furnishing premium, the demo payback for a 45 m2 South Jakarta unit is about 56 months (about 4.7 years), not 1.4 years. In Bekasi and BSD it is over 200 months. This still depends on the fit-out cost assumption and on the regex furnishing flag, so treat it as indicative.

## Known open items
- The model is Gradient Boosting, so there is no true hedonic layer (interpretable implicit prices) yet. Plan: OLS/Ridge on log rent plus SHAP.
- Building/project name, floor level, building age and condition are not in the model.
- Amenities are regex flags from short ad text ("not mentioned" is treated as "absent").
- Single source (Rumah123), apartments for rent, asking prices only.
- Cross-broker de-duplication is a heuristic and may drop genuinely identical units in the same building.
- `requirements.txt` still contains unused packages; CORS is still open (`allow_origins=["*"]`).
- Social post drafts and case study are archived under `docs/linkedin/` with verified out-of-fold metrics.
- Check the portal's terms and robots.txt before republishing raw listing data.
