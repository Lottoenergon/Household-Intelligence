# LinkedIn Case Study & Learning Reflection: Household Intelligence
## Greater Jakarta Rental Housing & PropTech Market Intelligence Engine

---

**Headline:** From Raw Scraped Listings to an Econometric AVM: My Capstone Journey Building an End-to-End PropTech Intelligence Engine 🏙️📈

---

Hello LinkedIn network and data analytics community! 👋

Coming from a **Chemical Engineering** background and transitioning into **Data Analytics**, one of the most valuable lessons I've embraced during my intensive training is:
> *"Real-world data is never packaged as a clean Kaggle CSV. Real value lies in handling noise, designing robust relational schemas, and translating empirical observations into actionable business logic."*

To put the fundamentals I've learned into practice, I designed and built an independent capstone project: **Household Intelligence** — an end-to-end PropTech Market Intelligence and Automated Valuation Model (AVM) engine analyzing 787 rental apartment listings across all **10 administrative regions of Greater Jakarta (Jabodetabek)**.

The primary objective was not just training a machine learning model, but understanding and implementing the entire lifecycle of data: from automated extraction and dimensional data warehousing to econometric modeling and sub-10ms user-facing deployment.

---

### 🛠️ What I Built & Key Technical Takeaways

#### 1. Ingestion & Real-World Data Cleansing
* Extracted 787 verified rental apartment listings across 10 Greater Jakarta administrative cities with rate-limiting and politeness delays.
* **Sanity Auditing:** Filtered out severe ad contamination—specifically multi-billion IDR purchase advertisements erroneously classified in rental feeds.
* **Regex NLP Normalization:** Extracted unit amenities (AC, Swimming Pool, Gym, Kitchen Set, Balcony) and standardized furnishing classifications (*Full Furnished*, *Semi*, *Unfurnished*) from free-text descriptions.

#### 2. Relational Dimensional Modeling (Star Schema in SQLite)
Rather than operating on flat CSV files, I structured the data warehouse following Kimball dimensional modeling:
* Designed a **Star Schema** centered on a fact table (`fact_rental_listings`) with 3 dimension tables (`dim_locations`, `dim_property_specs`, `dim_amenities`).
* Authored **6 compiled analytical SQL views** (including distance decay, transit accessibility premiums, and regional benchmarks) to streamline connection with Business Intelligence platforms (Looker Studio / Tableau).

#### 3. Econometric Hedonic Price Modeling (Rosen, 1974)
In urban economics, residential rent is treated as a composite bundle of characteristics rather than a single commodity:
* Applied logarithmic transformations $\ln(	ext{Rent})$ and $\ln(	ext{FloorSize})$ to capture the economic law of *diminishing marginal returns* (adding 10 m² to a 25 m² studio generates a vastly different marginal utility than adding 10 m² to a 150 m² unit).
* Trained and evaluated both *Ridge Regression* and a non-linear *Gradient Boosting Regressor*.
* **Validation Results:** Achieved a **5-Fold Cross-Validation $R^2 = 0.835$** (Full $R^2 = 0.959$) with a Mean Absolute Percentage Error (**MAPE**) of **13.7%** (MAE: ~IDR 1.11M) on noisy real-world listing data.

#### 4. Algorithmic Deal Hunter (Residual Z-Score)
* Computed standardized model residuals: $Z = \frac{\text{Actual Asking Rent} - \text{Fair Market Rent}}{\sigma_{\text{residual}}}$.
* Listings with $Z \le -0.75$ are flagged as **Bargain Deals** (identifying 39 genuine market anomalies offered by landlords at 15%–32% below equilibrium value).

#### 5. Commercial-Grade Standalone Web Application
Evolved beyond initial notebook and Streamlit prototypes to deploy a full-stack production architecture:
* **Backend:** REST API built with **FastAPI + Uvicorn** delivering sub-10ms query latency.
* **Frontend:** Interactive Single Page Application designed with the **Linear Design System** ("Midnight Precision Instrument"), featuring dual-user persona switching (*Rian Public Renter* vs *Bu Sarah Pro Investor* with interior fit-out payback metrics).

---

### 💡 Core Takeaway: Data Ethics & Reality Check
One of the most critical dilemmas I encountered was the **specific location variable**. On public real estate portals, brokers never publish exact door-to-door GPS coordinates.

Initially, it was tempting to generate random localized scatter pins. However, doing so would create a false illusion that the platform knows the private door address of each unit. As a responsible data practitioner, data integrity comes first:
> **I made the architectural decision to remove fictitious unit dots entirely and replace them with macro district/subdistrict centroid clusters (105 areas across Jabodetabek).**

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
