# LinkedIn Case Study & Learning Reflection: Household Intelligence
## Greater Jakarta Rental Housing & PropTech Market Intelligence Engine

---

**Headline:** From Raw Scraped Listings to an Econometric AVM: My Capstone Journey Building an End-to-End PropTech Intelligence Engine 🏙️📈

---

Hello LinkedIn network and data analytics community! 👋

Coming from a **Chemical Engineering** background and transitioning into **Data Analytics**, one of the most valuable lessons I've embraced during my intensive training is:
> *"Real-world data is never packaged as a clean Kaggle CSV. Real value lies in handling noise, designing robust relational schemas, and translating empirical observations into actionable business logic."*

To put the fundamentals I've learned into practice, I designed and built an independent capstone project: **Household Intelligence** — an end-to-end PropTech Market Intelligence and Automated Valuation Model (AVM) engine analyzing **728 verified, deduplicated rental apartment listings** across all **10 administrative jurisdictions of Greater Jakarta (Jabodetabek)**.

The primary objective was not just training a machine learning model, but understanding and implementing the entire lifecycle of data: from automated extraction and dimensional data warehousing to honest out-of-fold econometric evaluation and sub-10ms user-facing deployment.

---

### 🛠️ What I Built & Key Technical Takeaways

#### 1. Ingestion & Content-Based Deduplication
* Extracted 800 rental apartment listings across 10 Greater Jakarta administrative cities with polite rate-limiting.
* **Contamination Filtering:** Purged extreme ad contamination—specifically multi-billion IDR purchase advertisements erroneously classified into rental streams.
* **Cross-Broker Entity Resolution:** Real estate portals in Indonesia are heavily saturated with cross-broker duplicate postings (identical units posted with slightly altered titles). Applied composite deduplication across price, floor area, layout, and subdistrict, eliminating **59 duplicate listings** to reach a verified baseline of **728 unique listings**.
* **Regex NLP Normalization:** Extracted unit amenities (AC, Swimming Pool, Gym, Kitchen Set, Balcony) and standardized furnishing classifications (*Full Furnished*, *Semi*, *Unfurnished*) from unstructured text descriptions.

#### 2. Relational Dimensional Modeling (Star Schema in SQLite)
Rather than operating on flat CSV files, I structured the data warehouse following Kimball dimensional modeling:
* Designed a **Star Schema** centered on a fact table (`fact_rental_listings`) with 3 dimension tables (`dim_locations`, `dim_property_specs`, `dim_amenities`).
* Authored **6 compiled analytical SQL views** (including distance decay, transit accessibility benchmarks, and regional price/m² medians) to enable immediate BI reporting.

#### 3. Honest Econometric Hedonic Price Modeling (Rosen, 1974)
In urban economics, residential rent is treated as a composite bundle of characteristics rather than a single commodity:
* Applied logarithmic transformations `ln(Rent)` and `ln(FloorSize)` to capture the economic law of *diminishing marginal returns* (adding 10 m² to a 25 m² studio generates vastly different marginal utility than adding 10 m² to a 150 m² unit).
* **Honest Out-of-Fold Evaluation:** Resisted the trap of presenting inflated in-sample scores (`R² = 0.95`). Evaluated the Gradient Boosting Regressor through **repeated 5-Fold Cross-Validation (3 repeats)** and **GroupKFold** across unseen subdistricts, alongside a naive baseline:
  * Out-of-Fold Cross-Validation R²: `0.830` (beats naive baseline `0.737` and Ridge `0.753`)
  * Mean Absolute Error (MAE): `IDR 2.11M / mo`
  * Typical Median APE: `17.7%`
  * Unseen Subdistrict Generalization R²: `0.744`

#### 4. Algorithmic Deal Hunter (Log-Residual Z-Score)
* Instead of calculating residuals on raw Rupiah (which causes luxury units to skew standard deviation), residuals are measured on the **logarithmic scale**: `ln(Actual) - ln(Fair Market Est)`.
* Units with `Z <= -0.75` are categorized into **Bargain Deals** (identifying 139 candidate opportunities offered at statistically significant discounts below market equilibrium).

#### 5. Commercial-Grade Standalone Web Application
Evolved beyond basic notebook scripts to deploy a full-stack production architecture:
* **Backend:** REST API built with **FastAPI + Uvicorn** delivering sub-10ms query latency.
* **Frontend:** Interactive Single Page Application designed with the **Linear Design System** ("Midnight Precision Instrument"), featuring an integrated **Rental Market & Deal Explorer**, reactive subdistrict hotspots directory, and a dedicated **Pro Investor Portal** (Bu Sarah persona with interior fit-out payback metrics).

---

### 💡 Core Takeaway: Data Integrity Over False Precision
One of the most critical dilemmas I encountered was the **spatial coordinate variable**. On public real estate portals, brokers never publish exact door-to-door GPS coordinates.

Initially, placing individual dot markers on a map created a misleading illusion of GPS precision. As a responsible data practitioner:
> **I made the architectural decision to remove fictitious map dots entirely and replace them with a responsive Subdistrict Directory & Market Hotspot Grid (105 areas across Jabodetabek).**

Transparency regarding real-world data limitations is infinitely more valuable than flashy, misleading visual precision.

---

### 🙏 Open for Mentorship & Feedback!
As an aspiring **Junior Data Analyst / Analytics Engineer**, learning is a continuous process. I would deeply appreciate any constructive criticism, guidance, or suggestions from mentors, seniors, and practicing data professionals:

1. **On Feature Engineering:** For metropolitan apartment rental valuation in Southeast Asia, what additional spatial or economic features would you consider essential?
2. **On Handling Noisy Data:** What are industry best practices for resolving duplicate listings across multiple real estate brokerages (entity resolution)?
3. **On Pipeline Architecture:** What key improvements would you recommend to transition this SQLite Star Schema into enterprise cloud data warehouses like BigQuery or Snowflake?

The complete source code, SQL Star Schema DDL, econometric scripts, and interactive web application are available on GitHub:  
📁 **Repository:** https://github.com/Lottoenergon/Household-Intelligence

Thank you for reading and for your support! I would love to connect and exchange thoughts in the comments or via LinkedIn messaging. 🚀

---
#DataAnalytics #LearningInPublic #PropTech #DataEngineering #Python #FastAPI #SQL #MachineLearning #DataScience #HedonicPricing #CareerTransition #OpenToFeedback #TechCommunity
