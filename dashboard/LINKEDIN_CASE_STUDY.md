# LinkedIn Case Study & Learning Reflection: Household Intelligence
## Greater Jakarta Rental Housing & PropTech Market Intelligence Engine

---

### [VERSI 1: BAHASA INDONESIA (Rekomendasi untuk Jaringan LinkedIn Lokal)]

**Headline:** Dari Data Mentah Portal Properti ke Hedonic AVM: Refleksi Belajar Membangun PropTech Intelligence Engine untuk Pasar Sewa Jabodetabek 🏙️📊

---

Halo rekan-rekan dan para praktisi data di LinkedIn! 👋

Sebagai seseorang dengan latar belakang **Teknik Kimia** yang sedang berproses mendalami dunia **Data Analytics**, salah satu tantangan terbesar yang sering saya dengar adalah: 
> *"Dataset di dunia nyata itu tidak pernah sebersih dan serapi dataset tutorial atau kompetisi."*

Untuk menguji dan mengasah pemahaman analitika yang saya pelajari selama bootcamp dan belajar mandiri, saya memutuskan untuk mengerjakan proyek portofolio independen: **Household Intelligence** — sebuah platform *PropTech Market Intelligence* dan *Automated Valuation Model (AVM)* untuk membedah dinamika harga sewa apartemen di **10 wilayah Jabodetabek**.

Fokus utama saya dalam proyek ini bukan sekadar melatih model *machine learning*, melainkan memahami siklus data *end-to-end*: mulai dari pengumpulan data mentah, pemodelan relasional, hingga penyajian produk yang bernilai bagi pengguna nyata.

---

### 🛠️ Apa Saja yang Saya Pelajari & Bangun?

#### 1. Menghadapi "Kekotoran" Data Dunia Nyata (Data Ingestion & Cleaning)
* Mengekstraksi 787 listing apartemen aktif dari portal publik dengan menerapkan *rate-limiting* dan *politeness delay*.
* **Tantangan Sanity Check:** Banyak iklan jual properti bernilai miliaran rupiah yang "bocor" masuk ke kategori sewa. Saya merancang filter validasi ketat dan normalisasi sewa tahunan/harian ke standar bulanan (IDR/bulan).
* **NLP Keyword Extraction:** Menggunakan *regular expressions* untuk mengekstrak fasilitas spesifik (AC, Kolam Renang, Gym, Kitchen Set, Balkon) dan status kelengkapan perabot (*Full Furnished*, *Semi*, *Unfurnished*) dari deskripsi teks bebas.

#### 2. Merancang Gudang Data (Relational Star Schema di SQLite)
Agar data tidak hanya menumpuk dalam file CSV datar, saya mempraktikkan konsep *Data Warehousing*:
* Membangun **Star Schema** dengan 1 tabel fakta (`fact_rental_listings`) dan 3 tabel dimensi (`dim_locations`, `dim_property_specs`, `dim_amenities`).
* Mengompilasi **6 Analytical SQL Views** (seperti *distance decay*, *amenity premiums*, dan *benchmark wilayah*) untuk mempermudah integrasi dengan tools Business Intelligence (Tableau / Looker Studio).

#### 3. Ekonometrika & Machine Learning: Hedonic Pricing Model
Dalam ilmu ekonomi perkotaan (Urban Economics), sewa properti dipandang sebagai kumpulan nilai dari berbagai atribut (*Rosen, 1974*).
* Menerapkan transformasi logaritmik $\ln(\text{Rent})$ dan $\ln(\text{FloorSize})$ untuk menangkap hukum *diminishing marginal returns* (tambahan 10 m² pada unit studio memiliki nilai marjinal yang berbeda dengan unit penthouse).
* Membandingkan *Ridge Regression* dengan *Gradient Boosting Regressor*.
* **Hasil Evaluasi:** Model mencapai **5-Fold Cross Validation $R^2 = 0.835$** (Full $R^2 = 0.959$) dengan Mean Absolute Percentage Error (**MAPE**) **13.7%** (MAE: ~Rp 1.11 Juta) pada data listing pasar yang berisik (*noisy*).

#### 4. Algoritma Deteksi Diskon (Deal Hunter Radar)
* Menghitung nilai residual: $\text{Residual} = \text{Harga Aktual} - \text{Estimasi Harga Wajar}$.
* Menstandarisasi residual menjadi **Z-score** ($Z = \frac{\text{Residual}}{\sigma}$).
* Listing dengan $Z \le -0.75$ diklasifikasikan sebagai *Bargain Deals* (menemukan 39 unit apartemen yang ditawarkan pemilik dengan diskon 15%–32% di bawah harga ekuilibrium pasar).

#### 5. Eksekusi Produk: Standalone Web Application
Awalnya proyek ini dibuat dengan Streamlit. Namun, agar lebih mendekati standar produk komersial nyata, saya mentransisikannya menjadi aplikasi web mandiri:
* **Backend:** REST API berkecepatan tinggi menggunakan **FastAPI** (<10ms respons).
* **Frontend:** Single Page Application (SPA) berbasis *Linear Design System* ("Midnight Precision Instrument") dengan dua mode persona: *Pencari Sewa (Rian)* dan *Investor Pro (Bu Sarah)* yang dilengkapi kalkulator *payback* interior.

---

### 💡 Refleksi & Pembelajaran Penting: "Data Ethics & Reality Check"
Salah satu dilema terbesar yang saya temukan adalah **variabel lokasi spesifik**. Di portal properti publik, agen tidak pernah memberikan titik GPS presisi per pintu unit apartemen.

Awalnya saya sempat tergoda untuk memetakan koordinat acak di peta. Namun, saya menyadari hal itu memberikan ilusi palsu seolah-olah sistem mengetahui alamat rahasia tiap pintu kamar. Sebagai praktisi data, integritas adalah nomor satu:
> **Saya memutuskan menghapus titik-titik pin unit fiktif tersebut dan menggantinya dengan agregasi sentroid kawasan makro/kecamatan (105 kawasan se-Jabodetabek).**

Transparansi mengenai batasan data (*data limitations*) jauh lebih penting daripada visualisasi yang terlihat canggih tetapi menyesatkan.

---

### 🙏 Mohon Bimbingan & Masukan (Ask for Feedback)!
Karena saya masih dalam proses belajar dan aktif mengembangkan diri menuju peran **Junior Data Analyst / Analytics Engineer**, saya sangat mengharapkan kritik, saran, dan masukan konstruktif dari para senior, mentor, maupun rekan-rekan praktisi:

1. **Tentang Feature Engineering:** Untuk valuasi sewa apartemen di kota metropolitan seperti Jabodetabek, fitur atau variabel penting apa lagi yang menurut rekan-rekan krusial untuk dimasukkan?
2. **Tentang Penanganan Noisy Data:** Bagaimana *best practice* di industri PropTech dalam menangani listing duplikat dari multi-broker (*entity resolution*)?
3. **Tentang Struktur Pipeline & SQL:** Apakah pendekatan Star Schema di SQLite ini sudah cukup modular untuk transisi ke cloud data warehouse seperti BigQuery/Snowflake?

Seluruh kode sumber, skema database SQL, dokumentasi teknis, dan file *launcher* batch terbuka untuk ditinjau:
📁 **GitHub Repository:** https://github.com/Lottoenergon/Household-Intelligence

Terima kasih banyak atas waktu dan masukannya! Sangat terbuka untuk berdiskusi di kolom komentar atau via DM LinkedIn. 🚀

---
#DataAnalytics #LearningInPublic #PropTech #DataEngineering #Python #FastAPI #SQL #MachineLearning #DataScience #HedonicPricing #CareerTransition #OpenToFeedback #TechCommunity

---
---

### [VERSI 2: ENGLISH (For Global Tech Recruiters & Engineering Leads)]

**Headline:** From Noisy Scraped Listings to an Econometric AVM: My Capstone Journey Building an End-to-End PropTech Intelligence Engine 🏙️📈

---

Hello LinkedIn network and data analytics community! 👋

Coming from a **Chemical Engineering** background and transitioning into **Data Analytics**, one of the most valuable lessons I've embraced during my intensive training is:
> *"Real-world data is never packaged as a clean Kaggle CSV. Real value lies in handling noise, designing robust schemas, and translating empirical observations into actionable business logic."*

To put the fundamentals I've learned into practice, I designed and built an independent capstone project: **Household Intelligence** — an end-to-end PropTech Market Intelligence and Automated Valuation Model (AVM) engine analyzing 787 rental apartment listings across all **10 administrative regions of Greater Jakarta (Jabodetabek)**.

---

### 🏗️ Technical Pipeline Overview

1. **Automated Ingestion & Sanity Cleansing:**
   * Rate-limited ingestion pipeline handling pagination and raw JSON staging.
   * Filtered severe ad contamination (eliminating multi-billion purchase ads miscategorized under rental feeds).
   * Regex NLP extraction for 9 discrete amenities and furnishing tiers (*Full Furnished*, *Semi*, *Unfurnished*).

2. **Relational Dimensional Modeling (Star Schema in SQLite):**
   * Implemented a relational data warehouse layer: 1 fact table (`fact_rental_listings`) and 3 dimension tables (`dim_locations`, `dim_property_specs`, `dim_amenities`).
   * Authored **6 compiled analytical SQL views** for immediate Business Intelligence connectivity (Looker Studio / Tableau).

3. **Econometric Hedonic Price Modeling (Rosen, 1974):**
   * Formulated log-log regression ($\ln(\text{Rent}) \sim \ln(\text{FloorSize}) + \text{CBD\_Distance} + \text{Transit\_Distance} + \text{Amenities} + \text{City\_Dummies}$) to mirror the law of diminishing marginal returns.
   * Gradient Boosting Regressor achieved **5-Fold Cross-Validation $R^2 = 0.835$** (Full $R^2 = 0.959$) with a Mean Absolute Percentage Error (**MAPE**) of **13.7%** (MAE: ~IDR 1.11M).

4. **Deal Hunter Residual Scoring:**
   * Standardized model residuals ($Z = \frac{\text{Actual} - \text{Fair}}{\sigma_{\text{residual}}}$) to identify statistically undervalued units ($Z \le -0.75$), unearthing 39 genuine market bargains saving tenants IDR 2M–6M monthly.

5. **Production Standalone Web App:**
   * Pivoted from a rapid Streamlit prototype to a commercial-grade architecture: **FastAPI backend** (<10ms latency) and a modern Single Page Application styled after the *Linear Design System* ("Midnight Precision Instrument"), complete with dual persona views (Renter vs Investor ROI payback calculator).

---

### 💡 Key Learning: Data Ethics Over False Precision
In publicly scraped classifieds, brokers never disclose exact GPS coordinates per unit door. Rather than synthesizing misleading pin coordinates on a map, I chose **macro-district clustering (105 subdistricts across Jabodetabek)**. Acknowledging data boundaries and ensuring transparency is a fundamental duty of a responsible data analyst.

---

### 🙏 Seeking Constructive Mentorship & Feedback!
As an aspiring **Junior Data Analyst / Analytics Engineer**, learning never stops. I would love to hear thoughts from experienced data analysts, engineers, and real estate data scientists:

* What additional feature engineering would you recommend for urban rental valuation in Southeast Asian metropolitan areas?
* How does your team typically handle entity resolution and multi-broker listing deduplication in production?
* What are the most critical areas I should refine to bring this closer to enterprise data engineering standards?

Feel free to review the reproducible pipeline, SQLite schema, and live batch launcher:
🔗 **GitHub Repository:** https://github.com/Lottoenergon/Household-Intelligence

Looking forward to your constructive critique, advice, and connections! 🚀

---
#DataAnalytics #PropTech #DataEngineering #MachineLearning #Python #FastAPI #SQL #CareerTransition #Mentorship #OpenToFeedback