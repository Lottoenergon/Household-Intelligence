# LinkedIn Caption (Casual Storytelling Edition - English)
## Portfolio Project: Household Intelligence — Greater Jakarta PropTech Engine

---

Hey everyone on LinkedIn! 👋

Over the past few months, I decided to take a deliberate step forward and dive deeper into the world of data analytics.

The initial spark came straight from my daily job as a **Quality Control (QC) Specialist** in manufacturing. Day in and day out, I work with operational numbers: tracking reject rates for incoming raw materials and finished products, evaluating defect trends, and keeping process variance under control.

Combining that frontline manufacturing experience with what I learned during an intensive data analytics bootcamp, one realization became crystal clear: in today's fast-moving digital and AI-driven era, data fluency isn't just a nice-to-have skill—it has become a **mandatory skillset**.

To test myself and apply these concepts on noisy, unstructured real-world data (instead of sanitized tutorial CSVs), I decided to build a hands-on project from scratch: **analyzing apartment rental prices across 10 regions in Greater Jakarta (Jabodetabek)**.

I extracted public classified listings across major portals, leveraging automated workflows and AI tools to streamline the ingestion process.

Looking at that raw data, a simple question came up:
> *"Can we untangle the wild price differences across fragmented listings and formulate an objective, data-driven fair market valuation for any apartment?"*

As it turns out, urban economists solved this theoretical question decades ago with the **Hedonic Pricing Model** (Rosen, 1974). The core idea is that property price isn't just a single random tag—it's a composite bundle of characteristics: floor area, distance to Central Business Districts (CBD), proximity to MRT/commuter rail transit, and furnishing/amenity levels.

From that theoretical foundation, I designed and built an end-to-end platform called **Household Intelligence**:
1. **Data Cleaning & Sanity Checks:** Purged multi-billion purchase ads erroneously tagged under rentals, normalized rates to monthly IDR standards, and extracted furnishing tiers with regex NLP.
2. **Relational Data Warehouse:** Built a Kimball Star Schema in SQLite (fact table + 3 dimensions + 6 production analytical SQL views) designed for BI tools.
3. **Econometric Valuation & Deal Hunter:** Trained a non-linear Gradient Boosting Regressor (5-Fold Cross Validation R² = 0.835, MAPE = 13.7%) and used standardized residual Z-scores to spot 39 genuinely undervalued "Bargain Deals" (15%–32% discount).
4. **Modern Web Platform:** Deployed a high-performance **FastAPI backend** (<10ms) paired with an interactive Single Page Application styled after the sleek **Linear Design System**.

---

### 🙏 Seeking Your Constructive Feedback!

As someone actively learning, experimenting, and transitioning deeper into **Data Analytics**, I know this project is an early milestone. There are plenty of real-world edge cases to polish—especially handling ambiguous broker district titles, multi-broker deduplication, and expanding spatial variables.

I would love to get your thoughts, advice, and constructive critique:
* *What additional features would you prioritize when modeling metropolitan apartment rentals?*
* *From a data engineering or ML perspective, what areas should I refine to bring this closer to production enterprise standards?*

Everything is open-source and transparently documented on GitHub (clean pipeline, SQL Star Schema, batch launchers):  
🔗 **GitHub Repository:** https://github.com/Lottoenergon/Household-Intelligence

Every piece of feedback means a lot for my learning journey. Thank you so much, and let's connect in the comments! 🙏🚀

---
#DataAnalytics #LearningInPublic #QualityControl #CareerTransition #PropTech #Python #MachineLearning #SQL #FastAPI #DataScience #Mentorship #OpenToFeedback
