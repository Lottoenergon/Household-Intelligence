# Product Requirements Document (PRD)
## Household Intelligence: Greater Jakarta Rental Housing & PropTech Market Intelligence Platform

* **Document Version:** v0.3.0 (Commercial Architecture & Verified Pipeline)
* **Status:** Approved / Active
* **Author:** Afiatta Ilhan Saleh
* **Repository:** [https://github.com/Lottoenergon/Household-Intelligence](https://github.com/Lottoenergon/Household-Intelligence)
* **Target Audience:** Product Managers, Data Engineers, Full-Stack Developers, Real Estate Investors, Recruiters

---

## 1. Executive Summary & Vision

### 1.1 Vision Statement
Household Intelligence is an independent, commercial-grade PropTech market analytics engine and automated valuation model (AVM) designed to bring algorithmic transparency, pricing discipline, and high-velocity deal discovery to the Greater Jakarta (Jabodetabek) rental housing market.

### 1.2 The Market Problem
The residential rental market across Jabodetabek (Jakarta, Bogor, Depok, Tangerang, South Tangerang, Bekasi) suffers from severe structural inefficiencies:
1. **Information Asymmetry & Price Opacity:** Asking rents on classified portals vary wildly without clear empirical baselines. Landlords and brokers frequently price units arbitrarily based on speculation rather than intrinsic physical and spatial utility.
2. **Ad Clutter & Multi-Broker Duplicate Listings:** The same physical apartment unit is frequently cross-listed across multiple agencies with distorted descriptions, varying prices, and differing square footage.
3. **Spatial False Precision:** Portals and mapping widgets often display localized scatter points that falsely imply private door-to-door GPS coordinates, creating data mistrust.
4. **Investor Capital Allocation Friction:** Individual landlords and property investors (such as buy-to-let owners) lack quantitative tools to model interior fit-out payback periods and fair gross yields before committing capital.

### 1.3 Solution & Value Proposition
Household Intelligence bridges this gap with an end-to-end data product:
* **Rigorous Pipeline:** Ingestion of 800 raw listings pruned and content-deduplicated to **728 verified unique apartment units** across **10 administrative cities and 105 subdistricts**.
* **Star Schema Warehouse:** Relational dimensional modeling (`fact_rental_listings` + 3 dimensions + 6 pre-compiled SQL analytical views) to support enterprise BI tooling.
* **Econometric Hedonic Model (Rosen 1974):** Gradient Boosting valuation engine validated via **Out-of-Fold 5-Fold Cross-Validation** (R2 = 0.830, beating naive and ridge baselines), producing statistically rigorous fair market rent estimates and empirical 80% confidence intervals.
* **High-Density Linear Web Interface:** Sub-10ms FastAPI backend powering a dark-canvas Single Page Application with zero third-party map dependencies, featuring an integrated Market & Deal Explorer, interactive valuation simulator, and dedicated Pro Investor Portal.

---

## 2. User Personas & Core Journeys

| Persona | Role / Profile | Core Pain Point | Primary Journey & Feature Needs |
|---|---|---|---|
| **Rian** *(Urban Tenant)* | Tech worker / corporate professional moving closer to Sudirman CBD or transit corridor. Monthly budget IDR 4M - IDR 12M. | Fear of overpaying; overwhelmed by broker spam and fake listings. | 1. Explore directory by subdistrict and layout.<br>2. Filter by `⚡ Bargain Deals Radar` to identify statistically underpriced units.<br>3. Verify unit via `Smart Rent Simulator` before signing lease. |
| **Bu Sarah** *(Buy-to-Let Investor)* | Passive property investor owning unfurnished apartments in Tangerang Selatan / Jakarta Barat. | Unclear ROI on renovation; unsure whether spending IDR 40M on furnishing will yield positive return. | 1. Access gated `Pro Investor Portal`.<br>2. Simulate interior fit-out payback period (months to break-even).<br>3. Benchmark asset yields against regional per-m2 market rates. |
| **Data Recruiter / Hiring Lead** | Technical Lead / Hiring Manager evaluating candidates for Data Analyst / Analytics Engineer roles. | Tired of toy Kaggle notebooks with in-sample overfitting claims. | 1. Inspect clean Git commit history and honest out-of-fold validation metrics.<br>2. Run `pytest tests/` (18 passing tests) verifying relational DB integrity.<br>3. Review Star Schema SQL DDL and API contract. |

---

## 3. Product Architecture & Technical Specifications

```
  +-----------------------------------------------------------------------------------+
  |                             DATA INGESTION & PIPELINE                             |
  |  Web Scraping (800 Raw Units) -> Bounding Box Geo Filter -> Content Deduplication  |
  |                        Output: 728 Verified Units (CSV & DB)                      |
  +-----------------------------------------+-----------------------------------------+
                                            |
                                            v
  +-----------------------------------------------------------------------------------+
  |                            DATA WAREHOUSE & MODELING                              |
  |  - SQLite Star Schema (fact_rental_listings, dim_locations, dim_specs, dim_amen)  |
  |  - 6 Compiled SQL Views (regional benchmarks, distance decay, deal hunter)        |
  |  - Hedonic ML Engine: Gradient Boosting Regressor (Out-of-Fold R2 = 0.830)        |
  |  - Standardized Log Residual Scoring for Mispricing Detection (Z <= -0.75)        |
  +-----------------------------------------+-----------------------------------------+
                                            |
                                            v
  +-----------------------------------------------------------------------------------+
  |                        BACKEND REST API (FastAPI / Uvicorn)                       |
  |  /api/telemetry | /api/listings | /api/districts | /api/benchmarks | /api/simulate|
  |  Latency: <10ms local query response                                              |
  +-----------------------------------------+-----------------------------------------+
                                            |
                                            v
  +-----------------------------------------------------------------------------------+
  |                         STANDALONE SINGLE PAGE APPLICATION                        |
  |  - Linear Design System ("Midnight Precision Instrument" Dark Theme)              |
  |  - Tab 1: Rental Market & Deal Explorer (Directory + Feed + Commercial Advisory)  |
  |  - Tab 2: Smart Rent Valuation Simulator (AVM + Empirical 80% CI)                 |
  |  - Tab 3: Pro Investor Portal (Bu Sarah Payback Engine + Model Telemetry)         |
  +-----------------------------------------------------------------------------------+
```

### 3.1 Tech Stack
* **Language & Runtime:** Python 3.14 / MSYS Bash on Windows 11.
* **Data Processing & ML:** `pandas`, `numpy`, `scikit-learn` (1.9.1), `joblib`.
* **Database:** SQLite 3 with ACID relational star schema and compiled views.
* **Backend:** FastAPI (0.142.2), Uvicorn server (async ASGI), Pydantic validation.
* **Frontend:** Vanilla HTML5, CSS3 Custom Properties (Linear Design tokens), modern ES6+ async fetch (Zero NPM build bloat).
* **Testing:** Pytest (18 automated tests covering spatial bounding, model scoring, relational integrity, and single-source-of-truth syncing).

---

## 4. Detailed Functional Requirements

### 4.1 Global Telemetry Ribbon
* **FR-TEL-01:** Display 4 core aggregate KPI cards:
  1. `Total Monitored Units`: Exactly 728 verified units.
  2. `Median Monthly Rent`: IDR 6.0M / month.
  3. `Median Rate per m2`: IDR 126k / m2.
  4. `Bargain Deals Detected`: 139 units (19.1% of inventory).
* **FR-TEL-02:** Safe fallback formatting (`—`) for all metrics with zero tolerance for `undefined` or `NaN` strings in the client UI.

### 4.2 Module 1: Rental Market & Deal Explorer (Unified Tab 1)
* **FR-EXP-01 (Feed Mode Switching):** Segmented buttons at top:
  * `All Monitored Listings (728)`: Full inventory exploration.
  * `⚡ Bargain Deals Radar (139)`: Filters inventory strictly to mispriced units with Z <= -0.75.
* **FR-EXP-02 (Deal Tier Sub-Filters):** When in Deals Mode, user can filter by:
  * `All Deals`: All 139 units.
  * `🔥 Deep Value`: Units with discount > 25% (Z <= -1.2, 43 units).
  * `✨ Good Deals`: Units with discount 15% - 25% (-1.2 < Z <= -0.75, 96 units).
* **FR-EXP-03 (Dimensional Filters):**
  * City Jurisdiction (10 cities: Jakarta Selatan, Pusat, Barat, Timur, Utara, Tangerang Selatan, Tangerang, Depok, Bekasi, Bogor).
  * Subdistrict selector (dynamically populated based on active city).
  * Layout category (Studio, 1BR, 2BR, 3BR, 4BR+).
  * Budget slider (IDR 1M to IDR 100M+ with "All Budgets / No Limit" default).
  * Furnishing checkbox (`Full Furnished Only`).
* **FR-EXP-04 (Subdistrict Hotspots Directory):**
  * Renders 105 subdistrict cards in a clean auto-fill grid.
  * Displays unit count, median rent, rate per m2, and deal count.
  * Clicking any card filters the listings feed below instantly without page reload.
* **FR-EXP-05 (Listing Feed Cards):**
  * Clean dark-card layout showing location, title, physical specs (m2, layout, furnishing), and asking rent.
  * If the unit is a Bargain Deal:
    * Highlighted with Acid Lime border.
    * Displays 3-column micro-grid: `Asking Rent` | `Fair Est.` | `Savings %`.
  * Dedicated `View Listing ↗` button opening the verified original portal listing in a new browser tab.
* **FR-EXP-06 (Commercial Renter Advisory):**
  * Right sidebar contains practical commercial advice (IPL & maintenance check, AVM negotiation anchor, appliance audit, annual lease payment leverage) replacing static methodology text.

### 4.3 Module 2: Smart Rent Valuation Simulator (Tab 2)
* **FR-SIM-01 (Parameter Inputs):**
  * Administrative City (required).
  * Subdistrict / Kawasan (optional, calibrates baseline).
  * Floor Area in m2 (constrained to valid range 15 m2 - 350 m2).
  * Bedroom and Bathroom count.
  * Furnishing status (Unfurnished, Semi, Full Furnished).
  * Proximity sliders: Distance to Sudirman CBD (0 - 50 km) and Distance to Nearest Transit (0 - 20 km).
* **FR-SIM-02 (Model Valuation Output):**
  * Directly executes `models/hedonic_gb.joblib` via `/api/simulate` (no arbitrary manual multipliers).
  * Renders Fair Market Rent in IDR/month.
  * Renders Empirical 80% Confidence Interval (`ci_lower_idr` to `ci_upper_idr` based on out-of-fold error distribution).
  * Displays dynamic comparison against actual asking price if provided.

### 4.4 Module 3: Pro Investor Portal (Bu Sarah, Tab 3)
* **FR-INV-01 (Role-Based Access):**
  * Gated behind persona switch (Guest/Renter vs Bu Sarah Pro Investor).
  * Unlocked state saved in browser `localStorage`.
* **FR-INV-02 (Interior Fit-Out Payback Engine):**
  * Accepts fit-out capital expenditure assumption per m2 (default IDR 800,000/m2, fully editable).
  * Calculates incremental monthly rental uplift from furnishing based on empirical model premium (+13.9% adjusted).
  * Computes Payback Period in months (`Total Fit-Out Cost / Monthly Rental Uplift`).
  * Calculates Annual Gross Yield on Renovation.
* **FR-INV-03 (Model Telemetry & Diagnostic Transparency):**
  * Discloses model architecture (Gradient Boosting with log-transformed target).
  * Displays Out-of-Fold R2 (83.0%), Baseline Naive R2 (73.7%), and Unseen Subdistrict R2 (74.4%).
  * Lists top feature importances: Floor Size (67.9%), Distance to CBD (9.7%), Jakarta Selatan fixed effect (8.6%).

---

## 5. Data Governance, Ethics & Anti-False Precision

1. **Centroid-Based Spatial Mapping:**
   * Public classified ads in Indonesia do not expose street/door-level coordinates.
   * Fictitious random jitter scatter points are strictly forbidden. The system operates transparently on administrative subdistrict centroids.
2. **Transparent Geo Imputation:**
   * Distance metrics for listings lacking native coordinates are imputed from subdistrict or city medians, tracked explicitly via `geo_source` (disclosing that South Tangerang has 64% imputed coordinates).
3. **Log Residual Mispricing Scoring:**
   * To prevent luxury apartments (e.g. IDR 80M/mo) from distorting the standard deviation, residuals are computed in logarithmic space: `e = ln(Actual) - ln(Fair)`.
   * Standardized Z-scores ($Z = e / \sigma$) ensure equitable deal detection across budget studios and luxury penthouses alike.

---

## 6. Non-Functional Requirements & Acceptance Criteria

| Requirement | Target Benchmark | Verification Method |
|---|---|---|
| **API Response Time** | < 15ms local latency for `/api/listings` and `/api/simulate` | Automated benchmark tests via `pytest` & FastAPI testclient |
| **Single Source of Truth** | Zero hardcoded discrepancies between CSV, DB, API, UI, and README | `tests/test_consistency.py` automated test assertions |
| **Browser Compatibility** | Chrome, Edge, Safari, Firefox (modern desktop & tablet) | Headless browser execution via Playwright/CDP |
| **Startup Simplicity** | 1-Click execution on Windows 11 without CLI friction | `start_platform.bat` automated launcher on port 8000 |
| **Automated Testing Suite** | 100% test pass rate across all test modules | `pytest tests/ -q` -> 18 passed, 0 failed |

---

## 7. Product Release Milestones & Future Roadmap

* **Phase 1 (Completed - v0.1.0):** Data scraping, initial cleaning, Streamlit prototype, and exploratory EDA.
* **Phase 2 (Completed - v0.2.0):** Migration to FastAPI + Linear SPA, Star Schema in SQLite, and initial Hedonic model.
* **Phase 3 (Completed - v0.3.0):** Content deduplication (728 units), out-of-fold honest CV evaluation, single source of truth, automated pytest suite, removal of disruptive map in favor of high-density District Explorer, and Tab 1/Tab 2 unification.
* **Phase 4 (Next / Pillar 3 Transition):**
  * Automated periodic ingestion via GitHub Actions or Airflow/Prefect cron.
  * Migration of analytical views to BigQuery / Snowflake cloud warehouse.
  * Integration of Looker Studio embedded dashboard.
  * WhatsApp / Telegram Bot notification engine for instant deal alerts when a listing with $Z \le -1.2$ appears on the market.
