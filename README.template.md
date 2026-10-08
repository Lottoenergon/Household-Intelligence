# Household Intelligence: Jabodetabek Apartment Rental Price Model

<!-- AUTO-GENERATED from README.template.md by scripts/render_readme.py. Do not edit README.md by hand. -->

An end-to-end analytics project: scrape apartment **rental** listings across Greater Jakarta, clean and model them with a hedonic-style price model, and flag listings priced far from what the model expects.

> **Status: work in progress, portfolio project.** Data are *asking prices* from one public portal (Rumah123), not transaction prices. "Below estimate" means "cheaper than the model expects given the features it sees", **not** "a bargain". Read the limitations before relying on any number.

## 1. Results (all numbers generated from the pipeline output)

I scraped **{{n_raw}}** rental listings and kept **{{n_final}}** after cleaning: {{n_url_dups}} duplicate URLs, {{n_price_removed}} sale ads or invalid prices, and {{n_content_dups}} cross-broker duplicates were removed. The final set covers {{n_cities}} cities and {{n_subdistricts}} subdistricts of apartments for rent. The median asking rent is Rp {{median_rent_m}}M per month (Rp {{median_ppm2_k}}k per m²).

Two patterns stand out. Apartments within 7 km of Sudirman cost about **+{{tier_premium}}%** more per m² than ones 15–28 km out, and fully furnished units ask **+{{furn_raw}}%** more in raw medians. After controlling for size, location and amenities the gap is **+{{furn_adj}}%** — furnishing pays for itself roughly as much as the raw numbers suggest.

### Model accuracy (out-of-fold, never evaluated on training rows)

| Model | R² | MAE | MAPE | Median APE |
|---|---|---|---|---|
{{eval_table}}

* **Final model, known areas:** R² {{r2}}, typical error about {{medape}}% (median), mean error {{mape}}% (MAPE is inflated by cheap listings).
* **80% empirical range:** the actual asking rent was within {{iv_lo}}% / {{iv_hi}}% of the estimate for {{iv_level}}% of listings. This is a plain empirical range from out-of-fold residuals, not a formal prediction interval.
* The model beats the simple city-median baseline (R² {{naive_r2}}) but not by a huge margin. On **subdistricts it has never seen**, Gradient Boosting (R² {{group_gb_r2}}) is barely ahead of the baseline ({{group_naive_r2}}): much of its skill comes from recognising the area.
* In-sample R² is {{train_r2}}. It is shown only as an overfitting diagnostic and is **not** a performance claim.

### What the model weighs most (Gradient Boosting feature importance)

| # | Feature | Importance |
|---|---|---|
{{feature_table}}

Feature importance says what the model *uses*, not the price of an attribute. See "Limitations" for what is not yet a true hedonic estimate.

## 2. Deal radar

For each listing the "fair rent" is the **out-of-fold** model prediction. The score is the standardised log residual:

```text
z = ( ln(asking rent) - ln(model rent) ) / std( ln residuals )
z <= -1.5 deep below estimate | -1.5 < z <= -0.75 below estimate | |z| < 0.75 in line | z >= 0.75 above estimate
```

A log residual is used because pricing errors are proportional, so a Rp 2M miss on a Rp 3M unit matters more than on a Rp 40M unit.

**{{below_n}} listings ({{below_pct}}%) are below estimate** (median gap {{median_discount}}%), and **{{above_n}} ({{above_pct}}%) are above**. Because typical model error is around {{medape}}%, these are *candidates to verify*, not confirmed bargains. Extreme cases are more likely a data error or a missing variable (building, floor, age, condition) than a real deal.

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

Cleaning steps: price normalised to monthly rent (yearly/daily converted), sale ads removed, URL and content-based dedup, floor size bounded to 15–350 m² ({{n_floor_imputed}} missing sizes imputed by city and bedroom median), coordinates validated against a Jabodetabek bounding box.

SQLite star schema (`sql/schema.sql`): `fact_rental_listings`, `dim_locations`, `dim_property_specs`, `dim_amenities` and 6 analytical views.

### Rent per m² by city (sample, not population)

| City | Listings | Median rent per m² | Median rent | Coordinates imputed |
|---|---|---|---|---|
{{city_table}}

Scraping is capped by pages per city, so city sizes reflect the scraper, not the market.

## 4. Limitations (please read)

1. **Asking prices, one source, apartments for rent only.** No sale prices, no landed houses, no transactions.
2. **Coordinates:** the portal omits or corrupts some. Invalid ones (missing, or longitude copied from latitude) are replaced by the subdistrict, then city, median of valid coordinates. Overall {{geo_imputed_pct}}% of rows are imputed, and **{{tangsel_imputed_pct}}% of South Tangerang rows**, so distances there are approximate. Each row carries `geo_source`.
3. **Missing variables:** building/project name, floor level, building age and condition are not in the model. They drive a lot of apartment rent variation.
4. **Amenities come from regex on short ad text.** "Not mentioned" is treated as "absent". Furnishing is flagged for only {{furnished_share}}% of listings.
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
