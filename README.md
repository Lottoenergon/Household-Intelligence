# Greater Jakarta (Jabodetabek) Rental Housing & Market Intelligence Engine
## Automated Data Ingestion, Relational Star Schema, Hedonic Valuation (AVM) & PropTech Deal Radar

[![Status](https://img.shields.io/badge/Status-Platform%20in%20Active%20Development%20(v0.2--alpha)-yellow.svg)]()
[![Python](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/SQLite-Star%20Schema-green.svg)]()
[![Backend](https://img.shields.io/badge/Backend-FastAPI%20%2B%20Uvicorn-009688.svg)](https://fastapi.tiangolo.com/)
[![Frontend](https://img.shields.io/badge/Frontend-Linear%20Design%20System-black.svg)]()
[![Model](https://img.shields.io/badge/Model-Gradient%20Boosting%20Hedonic%20(R%C2%B2%200.835)-purple.svg)]()

> **⚠️ Development Status & Data Transparency Notice (v0.2-alpha)**  
> Platform ini berada dalam status **Active Development (Work-in-Progress)**.

---

## 1. Executive Summary & Market Insights

Household Intelligence adalah platform inteligensi pasar properti sewa dan radar valuasi otomatis (*Automated Valuation Model / AVM*) yang dirancang untuk menghadirkan transparansi harga sewa apartemen di 10 wilayah administratif Jabodetabek.

| Metrik Pasar | Nilai Terukur | Interpretasi Bisnis & Signifikansi Ekonometrika |
| :--- | :--- | :--- |
| **Monitored Inventory** | **787 verified rental units** | Tersebar di 10 kota (Jakarta Pusat, Selatan, Barat, Timur, Utara, Tangerang, Tangsel, Depok, Bekasi, Bogor) |
| **Jakarta Core CBD Rent** | **Rp 208,333 / m²** (Jaksel) / **Rp 190,972 / m²** (Jakpus) | Kepadatan komersial tertinggi; premi tarif per m² mencapai 1.7x – 2.0x lipat kota penyangga |
| **Outer Satellite Rent** | **Rp 107,407 / m²** (Bekasi) / **Rp 109,719 / m²** (Tangerang) | Koridor hunian komuter terjangkau; didominasi tipe Studio dan 2BR |
| **Spatial Distance Decay** | **+61.5% Price/m² Premium** | Unit di Tier 1 (<7km dari Sudirman CBD) rata-rata Rp 194.5k/m² vs Rp 122.2k/m² di Tier 3 (15–28km) |
| **Furnishing Premium** | **+26.8% per m²** | Unit Full Furnished memiliki selisih tarif bersih ~Rp 35.000/m² dibandingkan unit kosongan |
| **Hedonic Valuation Accuracy** | **CV R² = 0.835** (5-Fold Cross Validation) | Full dataset R² = 0.959, MAE = Rp 1,110,815 (MAPE = 13.7%) |
| **Statistically Undervalued Deals** | **39 unit terdeteksi (Z ≤ -0.75)** | Unit dengan harga penawaran pemilik 15% – 32% di bawah estimasi wajar pasaran |

---

## 2. Technical Pipeline Architecture

Platform mengadopsi arsitektur data komersial modern yang memisahkan layer ekstraksi, pergudangan relasional, model ekonometrika, dan antarmuka web berkecepatan tinggi:

```text
[Portal Properti Publik / Web Endpoints]
   │
   ▼
[1. Ingestion Engine (src/ingestion.py)]
   ├── Ekstraksi multi-region (10 wilayah Jabodetabek)
   ├── Session pooling & politeness rate-limiting (0.4s - 0.8s)
   └── Penyimpanan immutable raw payload (data/raw/jabodetabek_rental_raw.json)
   │
   ▼
[2. Transformation & Sanity Pipeline (src/transformation.py)]
   ├── Normalisasi tarif tahunan/harian ke ekuivalen sewa bulanan (IDR/bulan)
   ├── Filter ad-contamination (menyingkirkan listing jual multi-miliar yang nyasar ke feed sewa)
   ├── Kalkulasi jarak Haversine ke CBD Sudirman-Thamrin dan 11 hub transit KRL/MRT
   ├── Ekstraksi NLP regex untuk kelengkapan furnitur & 9 fasilitas unit
   └── Output terstandarisasi: data/processed/jabodetabek_rental_cleaned.csv (787 baris bersih)
   │
   ▼
[3. Econometric Hedonic Model & Deal Radar (src/market_intelligence.py)]
   ├── Feature engineering: Log-linear floor size, location fixed effects, spatial decay
   ├── 5-Fold Cross-Validated Gradient Boosting Regressor (CV R² = 0.835, MAPE = 13.7%)
   ├── Standardized Residual Scoring (Z-score) untuk mendeteksi unit salah harga (mispriced)
   └── Output evaluasi: data/processed/jabodetabek_rental_evaluated.csv
   │
   ▼
[4. Relational Data Warehouse / Star Schema (sql/schema.sql)]
   ├── SQLite Relational Star Schema:
   │     ├── fact_rental_listings (787 rows)
   │     ├── dim_locations (105 subdistricts / kawasan makro)
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
   ├── ESRI Enterprise Dark Gray Canvas (Peta sebaran makro kawasan bebas API key)
   ├── Switcher Dual Persona: Rian (Pencari Sewa Awam) vs Bu Sarah (Investor Pro)
   └── Kalkulator Payback Fit-Out Interior & Simulasi Harga Pasaran Realistis
```

---

## 3. Econometric Hedonic Pricing Valuation Model

Dalam disiplin urban economics dan real estate appraisal (Rosen 1974), nilai sewa properti dimodelkan sebagai fungsi kumpulan atribut karakteristik:

```text
ln(Rent_i) = β_0 + ∑ β_city * Dummy_City + β_size * ln(FloorSize_i) + β_bed * Bedrooms_i 
             + β_cbd * DistToCBD_i + β_transit * DistToTransit_i + ∑ γ_j * Amenity_ij + ε_i
```

### Bobot Kontribusi Fitur (Feature Importance):
1. **Luas Unit (`ln(floor_size_m2)`): 42.1%** - Penentu tunggal terbesar dari variasi nominal harga sewa bulanan.
2. **Jarak Spasial ke CBD Sudirman (`distance_to_cbd_km`): 28.4%** - Gradien penurunan harga (distance decay) semakin jauh dari pusat bisnis inti Jakarta.
3. **Location Fixed Effect (`target_city`): 14.8%** - Disparitas kemauan membayar antar-wilayah kota administratif.
4. **Kelengkapan Furnitur (`is_full_furnished`): 8.3%** - Premi langsung sebesar +26.8% per m² untuk unit siap huni (ready to move-in).
5. **Konfigurasi Kamar & Fasilitas Tambahan (`bedrooms`, `has_pool`, `has_ac`): 6.4%** - Pendorong utilitas marginal.

### Algoritma Deteksi Deal Hunter (Standardized Residual Z-Score):
Residual regresi mencerminkan selisih harga penawaran pemilik terhadap nilai wajar pasar:

```text
Residual_i = ActualRent_i - FairMarketRent_i
Deal_Score_Z_i = Residual_i / StdError(Residuals)
```

* **Z ≤ -1.5**: **Super Murah / Rare Deal** (Diskon pasaran >25%, anomali harga langka).
* **-1.5 < Z ≤ -0.75**: **Harga Bagus / Undervalued** (Diskon pasaran 15% – 25%).
* **-0.75 < Z < 0.75**: **Harga Wajar Pasaran** (Sesuai ekuilibrium pasar).
* **Z ≥ 1.5**: **Premium / Overpriced** (Penawaran di atas rata-rata utilitas).

---

## 4. Star Schema Database & SQL Analytical Layer

Database `data/processed/rental_intelligence.db` mengimplementasikan Star Schema relasional untuk memudahkan integrasi BI (Tableau, Looker Studio, Metabase):

```sql
-- DDL Cuplikan: Fact & Dimension Joins untuk Analisis Distance Decay
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
1. `view_city_market_benchmarks`: Agregasi inventaris, median sewa, tarif/m², dan rasio unit furnished per kota.
2. `view_urban_zone_distance_decay`: Mengukur gradien penurunan tarif per km dari Inner CBD (<7km) ke Satellite Ring (>28km).
3. `view_transit_proximity_premium`: Mengukur selisih tarif berdasarkan radius jalan kaki ke stasiun KRL/MRT (<1.5km vs >3km).
4. `view_layout_and_bedroom_matrix`: Breakdown tarif per m² dan median sewa pada tipe Studio, 1BR, 2BR, 3BR, 4BR+.
5. `view_top_undervalued_deals`: Saringan listing terverifikasi murah secara statistik (Z ≤ -0.75).
6. `view_amenity_hedonic_premiums`: Menghitung premi empiris AC, Kolam Renang, Gym, dan Furnitur.

---

## 5. Panduan Menjalankan Platform Secara Lokal

### Prasyarat
* Python 3.10 – 3.14
* Git

### 1. Clone & Setup Virtual Environment
```bash
git clone https://github.com/Lottoenergon/Household-Intelligence.git
cd Household-Intelligence

# Setup virtual environment
python -m venv .venv

# Aktivasi di Windows:
.venv\Scriptsctivate

# Aktivasi di Linux/macOS:
source .venv/bin/activate

# Install dependensi
pip install -r requirements.txt
```

### 2. Jalankan Platform (1-Click Launcher)
* Di Windows, cukup klik dua kali file **`start_platform.bat`**.
* Atau jalankan manual via terminal:
```bash
python -m uvicorn backend.server:app --host 0.0.0.0 --port 8080 --reload
```
Akses platform di browser Anda: **`http://localhost:8080`**.

---

## 6. Real-World Limitations & Ongoing Roadmap

### Keterbatasan Data Nyata (Real-World Nuances):
1. **Granularitas Spasial**: Portal listing agregator tidak mempublikasikan titik GPS per unit apartemen secara bebas; koordinat peta saat ini menggunakan **sentroid kawasan makro/kecamatan** untuk menjaga integritas data tanpa mengarang koordinat fiktif.
2. **Noise Judul Listing**: Listing baris sering kali mencantumkan nama kawasan tetangga yang lebih populer di judul iklan (misal mencantumkan "Kuningan" padahal unit berada di batas Setiabudi/Tebet).
3. **Deduplikasi Agen**: Satu unit apartemen sering kali diiklankan oleh lebih dari satu broker dengan harga sedikit bervariasi.

### Roadmap Pengembangan Selanjutnya:
* [ ] **Building Master Table**: Integrasi master database 500+ nama gedung apartemen resmi di Jabodetabek dengan koordinat gerbang terverifikasi.
* [ ] **Automated Deduplication Engine**: Fuzzy-matching teks judul + kombinasi luas m² + lantai untuk mendeteksi duplikasi multi-broker.
* [ ] **Cloud Data Warehouse Migration**: Migrasi pipeline ELT harian ke Google BigQuery / Snowflake dengan orkestrasi dbt.

---

## Author
* **Afiatta Ilhan Saleh** (Atta)
* Sarjana Teknik Kimia Universitas Sultan Ageng Tirtayasa (IPK 3.43)
* Intensive Data Analytics Distinction (89/100)
* Track Record: QC Statistical Process Control & Process Optimization, Industrial Automation, PropTech Market Intelligence.
