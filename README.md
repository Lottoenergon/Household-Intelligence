# Greater Jakarta (Jabodetabek) Rental Housing & Market Intelligence Engine

> **⚠️ Development Status & Data Transparency Notice (v0.2-alpha)**  
> This platform is currently in **Active Development (Work-in-Progress)**. All apartment rental listing data is ingested empirically as-is from public real estate classified portals across 10 administrative regions of Greater Jakarta (Jabodetabek). Spatial analytics and map visualizations utilize **macro district/subdistrict clusters (centroids)** rather than **fictitious door-to-door coordinates**, as real estate aggregator portals do not publish exact unit/tower coordinates publicly without direct broker mediation (WhatsApp). Regional calibrations, building entity resolution, and multi-broker deduplication are continuously being refined.

---

## 1. Executive Summary & Market Insights

**Household Intelligence** is an end-to-end PropTech market intelligence platform and Automated Valuation Model (AVM) designed to establish rental price transparency across the 10 administrative jurisdictions of Greater Jakarta (Jabodetabek).

| Market Metric | Measured Value | Economic & Analytical Significance |
| :--- | :--- | :--- |
| **Monitored Inventory** | **787 verified rental units** | Distributed across 10 jurisdictions (South, Central, West, East, North Jakarta, Tangerang, South Tangerang, Depok, Bekasi, Bogor) |
| **Jakarta Core CBD Rent** | **IDR 208,333 / m²** (Jaksel) / **IDR 190,972 / m²** (Jakpus) | Highest commercial density; commands 1.7x to 2.0x higher price per m² than commuter satellite cities |
| **Outer Satellite Rent** | **IDR 107,407 / m²** (Bekasi) / **IDR 109,719 / m²** (Tangerang) | Affordable suburban commuter corridors; high absorption of Studio and 2BR layouts |
| **Spatial Distance Decay** | **+61.5% Price/m² Premium** | Units in Tier 1 (<7km from Sudirman CBD) average IDR 194.5k/m² vs IDR 122.2k/m² in Tier 3 (15–28km) |
| **Furnishing Premium** | **+26.8% per m²** | Full Furnished units command a net empirical premium of ~IDR 35,000/m² over unfurnished units |
| **Hedonic Valuation Accuracy** | **CV R² = 0.835** (5-Fold Cross Validation) | Full dataset R² = 0.959, MAE = IDR 1,110,815 (MAPE = 13.7%) |
| **Statistically Undervalued Deals** | **39 units detected (Z ≤ -0.75)** | Units asking 15% – 32% below equilibrium fair market rent (IDR 4M – 6M monthly savings) |

---

## 2. Technical Pipeline Architecture

The platform implements a modern commercial analytics architecture decoupling web ingestion, relational data warehousing, econometric machine learning, and a sub-10ms web interface:

```text
[Public Property Portals / Web Endpoints]
   │
   ▼
[1. Ingestion Engine (src/ingestion.py)]
   ├── Multi-region extraction across 10 Greater Jakarta administrative cities
   ├── Connection pooling & politeness rate-limiting (0.4s - 0.8s jitter)
   └── Immutable raw JSON payload storage (data/raw/raw_rental_listings_staged.json)
   │
   ▼
[2. Transformation & Sanity Pipeline (src/transformation.py)]
   ├── Standardized monthly rate normalization (converting annual/daily to IDR/month)
   ├── Ad-contamination filtering (purging multi-billion IDR sale ads from rental feeds)
   ├── Haversine geospatial calculations (distance to Sudirman-Thamrin CBD & 11 transit hubs)
   ├── NLP regex extraction for furnishing status & 9 unit amenities
   └── Standardized output: data/processed/jabodetabek_rental_cleaned.csv (787 clean rows)
   │
   ▼
[3. Econometric Hedonic Model & Deal Radar (src/market_intelligence.py)]
   ├── Feature engineering: Log-linear floor size, location fixed effects, spatial decay
   ├── 5-Fold Cross-Validated Gradient Boosting Regressor (CV R² = 0.835, MAPE = 13.7%)
   ├── Standardized Residual Scoring (Z-score) for statistical underpricing detection
   └── Evaluation output: data/processed/jabodetabek_rental_evaluated.csv
   │
   ▼
[4. Relational Data Warehouse / Star Schema (sql/schema.sql)]
   ├── SQLite Relational Star Schema:
   │     ├── fact_rental_listings (787 rows)
   │     ├── dim_locations (105 subdistricts / macro areas)
   │     ├── dim_property_specs (277 physical configurations)
   │     └── dim_amenities (56 distinct amenity profiles)
   └── 6 Production Analytical SQL Views (benchmarks, distance decay, transit, deals radar)
   │
   ▼
[5. High-Performance REST API Backend (backend/server.py)]
   ├── FastAPI + Uvicorn (<10ms latency)
   ├── Endpoints: /api/telemetry, /api/districts, /api/listings, /api/benchmarks, /api/deals, /api/simulate
   └── Dual-mode serving (Public Tenant Persona vs Pro Investor Persona)
   │
   ▼
[6. Modern Web Platform (frontend/index.html)]
   ├── Linear Design System ("Midnight Precision Instrument" - Void #08090a, Acid Lime #e4f222)
   ├── ESRI Enterprise Dark Gray Canvas (Macro district bubble clusters, no API key required)
   ├── Dual-Persona Switcher: Rian (Public Renter) vs Bu Sarah (Pro Investor)
   └── Interior Fit-Out Payback Calculator & Realistic Market Pricing Simulator
```

---

## 3. Econometric Hedonic Pricing Valuation Model

In urban economics and real estate appraisal (Rosen, 1974), market rent is modeled as a bundle of composite utility attributes rather than a single homogeneous good:

```text
ln(Rent_i) = β_0 + ∑ β_city * Dummy_City + β_size * ln(FloorSize_i) + β_bed * Bedrooms_i 
             + β_cbd * DistToCBD_i + β_transit * DistToTransit_i + ∑ γ_j * Amenity_ij + ε_i
```

### Statistical Feature Importances:
1. **Floor Area (`ln(floor_size_m2)`): 42.1%** - The single largest determinant of nominal monthly rental yield (diminishing marginal returns captured via log transform).
2. **Geographic Proximity to CBD (`distance_to_cbd_km`): 28.4%** - Continuous distance decay per kilometer away from Jakarta's central business core.
3. **Location Fixed Effect (`target_city`): 14.8%** - Structural inter-city willingness-to-pay divergence (Jaksel & Jakpus commanding top quartile).
4. **Furnishing Quality (`is_full_furnished`): 8.3%** - Direct cash premium (+26.8% per m²) for move-in-ready units.
5. **Layout & Specific Amenities (`bedrooms`, `has_pool`, `has_ac`): 6.4%** - Incremental marginal utilities.

### Deal Hunter Algorithm (Standardized Residual Z-Score):
The prediction residual measures the exact variance between the landlord's asking price and fair market equilibrium:

```text
Residual_i = ActualRent_i - FairMarketRent_i
Deal_Score_Z_i = Residual_i / StdError(Residuals)
```

* **Z ≤ -1.5**: **Deep Value Deal** (Heavy discount >25%, rare statistical bargain).
* **-1.5 < Z ≤ -0.75**: **Good Deal** (Fairly priced with 15%–25% discount).
* **-0.75 < Z < 0.75**: **Fair Market Price** (Within standard pricing band).
* **Z ≥ 1.5**: **Premium / Overpriced** (High luxury mark-up above attribute utility).

---

## 4. Star Schema Database & SQL Analytical Layer

The database `data/processed/rental_intelligence.db` implements a dimensional model designed for BI tools (Looker Studio, Tableau, Power BI) and SQL analytics:

```sql
-- Sample View: Distance Decay from Jakarta Core CBD
SELECT
    l.urban_zone,
    COUNT(f.listing_key) AS inventory_count,
    ROUND(AVG(l.distance_to_cbd_km), 1) AS avg_cbd_km,
    ROUND(AVG(f.price_per_m2_idr), 0) AS avg_price_m2_idr
FROM fact_rental_listings f
JOIN dim_locations l ON f.location_key = l.location_key
GROUP BY l.urban_zone
ORDER BY avg_cbd_km ASC;
```

### 6 Production SQL Views:
1. `view_city_market_benchmarks`: Aggregates inventory count, median rent, price/m², and full-furnished share across 10 cities.
2. `view_urban_zone_distance_decay`: Quantifies the spatial rent gradient from Core CBD (<7km) to Outer Satellites (>28km).
3. `view_transit_proximity_premium`: Measures price differences across transit accessibility tiers (<1.5km walking vs >3km commuter feeder).
4. `view_layout_and_bedroom_matrix`: Breakdown of price per m² and rental distributions across Studio, 1BR, 2BR, 3BR, and 4BR+.
5. `view_top_undervalued_deals`: Filtered view of listings with statistically verified underpricing (Z ≤ -0.75).
6. `view_amenity_hedonic_premiums`: Measures the empirical percentage premiums of Air Conditioning, Swimming Pool, Gym, and Furnishing status.

---

## 5. How to Run Locally

### Prerequisites
* Python 3.10 – 3.14
* Git

### 1. Clone & Set Up Virtual Environment
```bash
git clone https://github.com/Lottoenergon/Household-Intelligence.git
cd Household-Intelligence

# Create virtual environment
python -m venv .venv

# Activate on Windows:
.venv\Scripts\activate

# Activate on Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Launch Platform (1-Click Launcher)
* On Windows, simply double-click **`start_platform.bat`**.
* Or execute manually via terminal:
```bash
python -m uvicorn backend.server:app --host 0.0.0.0 --port 8080 --reload
```
Open your web browser at: **`http://localhost:8080`**.

---

## 6. Real-World Limitations & Ongoing Roadmap

### Real-World Data Nuances:
1. **Spatial Granularity**: Classified listing portals do not publish exact unit/tower GPS coordinates openly; current maps utilize **macro district/subdistrict centroids** to maintain data integrity without inventing fictional coordinates.
2. **Listing Title Noise**: Classified headlines frequently reference neighboring prestigious districts (e.g., labeling an ad as "Kuningan" when located on the boundary of Setiabudi/Tebet).
3. **Multi-Broker Duplication**: Multiple real estate agents frequently post identical units with minor price discrepancies.

### Development Roadmap:
* [ ] **Building Master Table**: Integration of a verified master database of 500+ official apartment buildings in Greater Jakarta with precise entrance gate coordinates.
* [ ] **Automated Deduplication Engine**: Fuzzy text matching (title keywords + floor size + floor level) to resolve multi-broker duplicates.
* [ ] **Cloud Data Warehouse Migration**: Migrating daily ELT ingestion into Google BigQuery / Snowflake orchestrated via dbt.

---

## Author
* **Afiatta Ilhan Saleh**
