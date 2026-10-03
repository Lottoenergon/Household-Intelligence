# Greater Jakarta (Jabodetabek) Rental Housing & Market Intelligence Engine
## Automated Data Ingestion, Relational Star Schema, Hedonic Valuation & PropTech Deal Finder

[![Python](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/SQLite-Star%20Schema%20%26%20Views-green.svg)]()
[![Dashboard](https://img.shields.io/badge/Streamlit-Interactive%20App-red.svg)](https://streamlit.io/)
[![Machine Learning](https://img.shields.io/badge/scikit--learn-Hedonic%20Valuation-orange.svg)]()

Production-grade real estate analytics pipeline demonstrating **end-to-end data acquisition from unstructured public web feeds**, automated schema normalization, relational database modeling, and econometrics-based valuation to detect undervalued rental properties across Greater Jakarta (Jabodetabek).

---

## 1. Business Problem & Executive Value Proposition

In fast-growing metropolitan rental markets like Greater Jakarta (Jakarta, Tangerang, Depok, Bekasi, Bogor), property pricing exhibits severe market opacity:
1. **Unstructured & Fragmented Pricing:** Listings alternate arbitrarily between monthly, yearly, and daily rates, frequently contaminated with primary development property sales advertisements.
2. **Feature Confounding:** High absolute rental prices often mask poor area efficiency (price per square meter), while budget units may carry hidden premiums due to sub-district proximity to transit corridors (KRL / MRT / LRT).
3. **The "Deal Hunter" Dilemma:** Tenants and corporate relocation analysts lack an objective benchmark to determine whether an apartment is genuinely undervalued or overpriced relative to its physical features (size, layout, furnishing, transit proximity).

**Solution Delivered:** An automated intelligence engine that continuously extracts, normalizes, evaluates fair market price, and flags undervalued deals (discount >25% vs market baseline).

---

## 2. Technical Pipeline Architecture

```text
[Public Property Listing Feeds (10 Greater Jakarta Administrative Cities)]
   │
   ▼
[1. Ingestion Engine (src/ingestion.py)]
   ├── Defensive HTTP session handling & randomized User-Agent rotation
   ├── Exponential backoff rate-limit recovery (HTTP 429 / 5xx tolerance)
   └── Raw JSON staging cache (data/raw/raw_rental_listings_staged.json)
   │
   ▼
[2. Transformation & NLP Feature Engineering (src/transformation.py)]
   ├── Price standardization into monthly IDR equivalent (annualized / daily conversion)
   ├── Primary sales ad filtering & commercial outlier removal (<Rp 500k or >Rp 200 Jt/mo)
   ├── NLP keyword extraction for amenities (Full/Semi-Furnished, AC, WiFi, Pool, Transit proximity)
   └── Floor size imputation & calculation of Price / m² (Core real estate metric)
   │
   ▼
[3. Relational Data Warehouse (sql/schema.sql)]
   ├── Star Schema hosted on SQLite (data/processed/rental_intelligence.db):
   │     ├── fact_rental_listings
   │     ├── dim_locations
   │     └── dim_specifications
   └── 4 Analytical SQL Views (view_city_rental_benchmarks, view_top_undervalued_deals, etc.)
   │
   ▼
[4. Hedonic Pricing Valuation Engine (src/market_intelligence.py)]
   ├── Gradient Boosting Regressor (R² = 0.944, MAE = Rp 1.09 Juta)
   ├── Fair market value estimation & Valuation Discount % calculation
   └── Classification into High Value Deal (>25% discount), Fair Deal, or Overpriced
   │
   ▼
[5. Interactive Web Application (Streamlit app.py)]
   ├── Multi-parameter filtering (City, Budget Slider, Bedrooms, Valuation Status)
   ├── Geographic geospatial coordinate mapping
   └── Real-time Deal Finder Radar with direct listing deep-links
```

---

## 3. Market Intelligence Highlights (Jabodetabek)

Across **295 verified, clean residential rental units** spanning 10 administrative regions:

| City / Region | Active Units Sampled | Median Monthly Rent | Median Rent / m² | Key Characteristics |
| :--- | :--- | :--- | :--- | :--- |
| **Jakarta Selatan** | 29 | Rp 16,500,000 | **Rp 208,333 / m²** | Highest price density; luxury expatriate & CBD hub |
| **Jakarta Pusat** | 29 | Rp 11,000,000 | **Rp 190,972 / m²** | Commercial core; high proportion of full-furnished studio & 1BR |
| **Bogor** | 30 | Rp 5,000,000 | **Rp 138,634 / m²** | Suburban lifestyle hubs & residential corridors |
| **Jakarta Utara** | 28 | Rp 4,583,333 | **Rp 126,949 / m²** | Coastal & waterfront complexes (PIK, Kelapa Gading) |
| **Tangerang Selatan** | 30 | Rp 4,250,000 | **Rp 119,335 / m²** | Modern master-planned developments (BSD, Bintaro) |
| **Jakarta Barat** | 30 | Rp 4,166,667 | **Rp 110,914 / m²** | High volume of mid-tier commuter apartments |
| **Depok** | 29 | Rp 2,500,000 | **Rp 109,756 / m²** | Student & university corridor (Margonda UI); lowest absolute median rent |
| **Tangerang** | 30 | Rp 3,500,000 | **Rp 109,719 / m²** | Industrial & airport transit proximity |
| **Bekasi** | 30 | Rp 4,166,667 | **Rp 107,407 / m²** | Eastern commuter corridor; competitive price per m² |
| **Jakarta Timur** | 30 | Rp 4,208,333 | **Rp 105,159 / m²** | Most affordable price per m² across DKI Jakarta |

### Key Economic Insights:
* **The Centrality Premium:** Renting in Jakarta Selatan or Jakarta Pusat commands an average **+90% premium per m²** compared to peripheral commuter hubs (Depok, Tangerang, Bekasi).
* **The Furnishing Dividend:** Full-furnished units command an average price of **Rp 157,000 / m²**, compared to **Rp 114,000 / m²** for bare/unfurnished units—a net premium of ~37.7%.

---

## 4. Top Undervalued Deals Detected ("Deal Hunter")

The Hedonic Pricing Engine flagged **71 units (24.1% of inventory)** priced at a >10% discount relative to their location, area, and amenity profile:

* **Top Deal 1 (Jakarta Utara):** 2BR Tokyo Riverside PIK 2 | Actual: Rp 1,666,667/mo | Fair Market Est: Rp 3,452,837/mo (**51.7% Undervalued**)
* **Top Deal 2 (Jakarta Barat):** Condohouse Green Royal Semanan | Actual: Rp 2,750,000/mo | Fair Market Est: Rp 5,291,823/mo (**48.0% Undervalued**)
* **Top Deal 3 (Depok):** Margonda Residence 2 (Furnished) | Actual: Rp 2,000,000/mo | Fair Market Est: Rp 3,399,441/mo (**41.2% Undervalued**)

---

## 5. How to Run Locally

### 1. Setup Environment
```bash
# Clone the repository
git clone https://github.com/Lottoenergon/jabodetabek-rental-intelligence.git
cd jabodetabek-rental-intelligence

# Initialize virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Execute Automated Pipeline
```bash
# Runs Transformation, Valuation Modeling, and SQLite Database Ingestion
python run_pipeline.py

# Optional: To crawl fresh live web data across all 10 cities:
python run_pipeline.py --fresh-crawl
```

### 3. Launch Interactive Streamlit Dashboard
```bash
streamlit run app.py
```
*The interactive dashboard will open automatically in your browser at `http://localhost:8501`.*

---

## 6. Project Structure

```text
jabodetabek-rental-intelligence/
├── README.md                          <- Project documentation & market findings
├── requirements.txt                   <- Python environment dependencies
├── run_pipeline.py                    <- Master orchestrator
├── app.py                             <- Streamlit interactive web dashboard
├── sql/
│   └── schema.sql                     <- Star Schema DDL & 4 Analytical SQL Views
├── src/
│   ├── ingestion.py                   <- Web scraper with rate limiting & error handling
│   ├── transformation.py              <- Cleaning, currency normalization & NLP feature vectors
│   └── market_intelligence.py         <- Hedonic pricing model & database ingestion
└── data/
    ├── raw/
    │   └── raw_rental_listings_staged.json <- Staged raw web payloads
    └── processed/
        ├── jabodetabek_rental_cleaned.csv  <- Clean tabular listings
        ├── jabodetabek_rental_evaluated.csv<- Evaluated records with discount %
        └── rental_intelligence.db          <- Relational SQLite database
```

---

## 7. Author & Contact
* **Afiatta Ilhan Saleh (Atta)**
* B.Eng. in Chemical Engineering | Data Analyst & Analytics Engineer
* Email: [afiattailhan.ai@gmail.com](mailto:afiattailhan.ai@gmail.com)
* GitHub: [Lottoenergon](https://github.com/Lottoenergon)
