# Household Intelligence: Jabodetabek Apartment Rental Price Model

<!-- AUTO-GENERATED from README.template.md by scripts/render_readme.py. Do not edit README.md by hand. -->

An end-to-end analytics project: scrape apartment **rental** listings across Greater Jakarta, clean and model them with a hedonic-style price model, and flag listings priced far from what the model expects.

> **Status: work in progress, portfolio project.** Data are *asking prices* from one public portal (Rumah123), not transaction prices. "Below estimate" means "cheaper than the model expects given the features it sees", **not** "a bargain". Read the limitations before relying on any number.

## 1. Results (all numbers generated from the pipeline output)

I scraped **3729** rental listings and kept **2822** after cleaning: 0 duplicate URLs, 20 sale ads or invalid prices, and 789 cross-broker duplicates were removed. The final set covers 10 cities and 132 subdistricts of apartments for rent. The median asking rent is Rp 5.5M per month (Rp 132k per m²).

Two patterns stand out. Apartments within 7 km of Sudirman cost about **+68.0%** more per m² than ones 15–28 km out, and fully furnished units ask **+3.2%** more in raw medians. After controlling for size, location and amenities the gap is **+1.9%** — furnishing pays for itself roughly as much as the raw numbers suggest.

### Model accuracy (out-of-fold, never evaluated on training rows)

| Model | R² | MAE | MAPE | Median APE |
|---|---|---|---|---|
| **Known areas (5-fold CV x3 repeats)** | | | | |
| Baseline: city median price/m² x size | 0.685 | Rp 3.24M | 34.8% | 23.4% |
| Ridge regression | 0.677 | Rp 3.20M | 33.5% | 23.2% |
| Gradient Boosting (final model) | 0.759 | Rp 2.61M | 28.1% | 19.2% |
| **Unseen subdistricts (GroupKFold)** | | | | |
| Baseline: city median price/m² x size | 0.679 | Rp 3.30M | 35.3% | 24.1% |
| Ridge regression | 0.671 | Rp 3.25M | 34.1% | 23.5% |
| Gradient Boosting (final model) | 0.698 | Rp 3.08M | 33.4% | 23.2% |

* **Final model, known areas:** R² 0.759, typical error about 19.2% (median), mean error 28.1% (MAPE is inflated by cheap listings).
* **80% empirical range:** the actual asking rent was within -33% / +46% of the estimate for 80% of listings. This is a plain empirical range from out-of-fold residuals, not a formal prediction interval.
* The model beats the simple city-median baseline (R² 0.685) but not by a huge margin. On **subdistricts it has never seen**, Gradient Boosting (R² 0.698) is barely ahead of the baseline (0.679): much of its skill comes from recognising the area.
* In-sample R² is 0.825. It is shown only as an overfitting diagnostic and is **not** a performance claim.

### What the model weighs most (Gradient Boosting feature importance)

| # | Feature | Importance |
|---|---|---|
| 1 | Floor area (log m²) | 81.0% |
| 2 | Distance to CBD | 8.9% |
| 3 | Distance to nearest transit hub | 4.1% |
| 4 | City: Jakarta Selatan | 1.6% |
| 5 | Bedrooms | 1.1% |
| 6 | is_semi_furnished | 0.4% |

Feature importance says what the model *uses*, not the price of an attribute. See "Limitations" for what is not yet a true hedonic estimate.

## 2. Deal radar

For each listing the "fair rent" is the **out-of-fold** model prediction. The score is the standardised log residual:

```text
z = ( ln(asking rent) - ln(model rent) ) / std( ln residuals )
z <= -1.5 deep below estimate | -1.5 < z <= -0.75 below estimate | |z| < 0.75 in line | z >= 0.75 above estimate
```

A log residual is used because pricing errors are proportional, so a Rp 2M miss on a Rp 3M unit matters more than on a Rp 40M unit.

**464 listings (16.4%) are below estimate** (median gap 35.5%), and **463 (16.4%) are above**. Because typical model error is around 19.2%, these are *candidates to verify*, not confirmed bargains. Extreme cases are more likely a data error or a missing variable (building, floor, age, condition) than a real deal.

## 3. Pipeline

```text
Rumah123 listing pages ──► src/ingestion.py        raw JSON (data/raw)
                       ──► src/transformation.py   cleaning, dedup, geo validation, regex amenities, distances
                       ──► src/market_intelligence.py   out-of-fold evaluation, model, deal scores, SQLite star schema,
                                                         models/hedonic_gb.joblib, market_summary.json
                       ──► backend/server.py       FastAPI: loads the SAME saved model for /api/simulate
                       ──► frontend/index.html     dashboard; every number is fetched from the API
                       ──► scripts/render_readme.py   this README
```

Cleaning steps: price normalised to monthly rent (yearly/daily converted), sale ads removed, URL and content-based dedup, floor size bounded to 15–350 m² (2 missing sizes imputed by city and bedroom median), coordinates validated against a Jabodetabek bounding box.

SQLite star schema (`sql/schema.sql`): `fact_rental_listings`, `dim_locations`, `dim_property_specs`, `dim_amenities` and 6 analytical views.

### Rent per m² by city (sample, not population)

| City | Listings | Median rent per m² | Median rent | Coordinates imputed |
|---|---|---|---|---|
| Jakarta Selatan | 382 | Rp 221k | Rp 20.4M | 52% |
| Jakarta Pusat | 375 | Rp 192k | Rp 12.0M | 50% |
| Bogor | 150 | Rp 148k | Rp 4.5M | 9% |
| Tangerang Selatan | 191 | Rp 131k | Rp 6.2M | 66% |
| Jakarta Barat | 203 | Rp 123k | Rp 6.5M | 17% |
| Depok | 327 | Rp 116k | Rp 3.1M | 51% |
| Jakarta Timur | 236 | Rp 113k | Rp 4.2M | 33% |
| Bekasi | 367 | Rp 112k | Rp 3.5M | 52% |
| Tangerang | 311 | Rp 107k | Rp 3.8M | 38% |
| Jakarta Utara | 280 | Rp 107k | Rp 5.0M | 38% |

Scraping is capped by pages per city, so city sizes reflect the scraper, not the market.

## 4. Limitations (please read)

1. **Asking prices, one source, apartments for rent only.** No sale prices, no landed houses, no transactions.
2. **Coordinates:** the portal omits or corrupts some. Invalid ones (missing, or longitude copied from latitude) are replaced by the subdistrict, then city, median of valid coordinates. Overall 43.1% of rows are imputed, and **66% of South Tangerang rows**, so distances there are approximate. Each row carries `geo_source`.
3. **Missing variables:** building/project name, floor level, building age and condition are not in the model. They drive a lot of apartment rent variation.
4. **Amenities come from regex on short ad text.** "Not mentioned" is treated as "absent". Furnishing is flagged for only 48.0% of listings.
5. **Gradient Boosting has no coefficients.** For implicit prices use the OLS layer (`/api/hedonic`); its out-of-fold R2 is lower than GB, so it is for interpretation, not valuation. The "model-adjusted" furnishing premium from GB is the average change in prediction when the flag is switched.
6. **Cross-broker duplicates** are removed with a heuristic (same price, size, bedrooms, bathrooms and location), which can also drop genuinely identical units in one building.
7. The fit-out payback calculator uses a **user-supplied cost assumption** (default Rp 1.2M per m², not derived from data).
8. Check the portal's terms and robots.txt before re-scraping or republishing listing data.

## 5. Run locally

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run_pipeline.py            # cleans, trains, writes model + metrics + this README (add --scrape to re-ingest)
python scripts/clean_listing_titles.py   # re-apply editorial titles: the pipeline regenerates the CSVs from scratch and drops raw_title / canonical_apartment
python -m uvicorn backend.server:app --port 8000    # open http://localhost:8000
```

Tests: `pip install -r requirements-dev.txt && python -m pytest tests -q` (includes checks that the API, UI and this README agree with the pipeline output).

## 6. Roadmap

- [x] Interpretable hedonic layer: OLS on log rent (HC1 SE, 95% CI) gives implicit prices per attribute (`/api/hedonic`)
- [x] Building/project entity resolution from listing titles: registry-driven matcher (`src/entity_resolution.py`, 173 projects in `data/property_registry.json`). Conservative: a listing resolves only on an exact alias or a distinctive-token match in the title/URL; anything ambiguous stays `Unresolved`. Not yet wired into the CSV/API
- [x] SHAP for the Gradient Boosting model (the OLS layer already gives implicit prices)
- [ ] Wider validation: more sources, repeated scrapes over time, price trends
- [x] Cleaner dependency list (`requirements.txt` lists `requests` and `beautifulsoup4`, which were imported but missing) and CORS hardening (same-origin by default)

## Author

Afiatta Ilhan Saleh
