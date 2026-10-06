/**
 * i18n.js
 * Internationalization & Bilingual Localization Engine (Indonesian & English)
 */

const I18N_DICTIONARY = {
    id: {
        // Brand & Topbar
        brand_tagline: "// Panduan sewa & radar properti Jabodetabek",
        topbar_status_active: "Unit aktif dipantau",
        topbar_login_full: "Masuk / Akses investor pro",
        topbar_login_mobile: "Akses pro",
        topbar_signout: "Keluar",
        topbar_active_profile: "Profil aktif:",
        investor_pro: "investor pro",

        // Metric Ribbon
        kpi_units_label: "Total unit dipantau",
        kpi_units_delta: "10 wilayah di Jabodetabek",
        kpi_rent_label: "Median sewa bulanan",
        kpi_rent_delta: "Benchmark pasar terkini",
        kpi_m2_label: "Tarif median per m²",
        kpi_m2_delta: "Biaya efektif ruang",
        kpi_bargains_label: "Peluang unit hemat",
        kpi_bargains_delta: "Di bawah estimasi wajar model",

        // Tab Navigation
        tab_map: "01 // Radar pasar & explorer listing",
        tab_simulator: "02 // Simulator valuasi sewa pintar",
        tab_investor: "03 // Portal investor pro (Bu Sarah)",
        badge_locked: "Pro",
        badge_unlocked: "Terbuka",

        // Tab 1: Filters & Explorer
        filter_mode_label: "Mode feed:",
        filter_mode_all: "Semua unit aktif",
        filter_mode_deals: "⚡ Radar unit hemat",
        deal_tier_all: "Semua deal",
        deal_tier_deep: "🔥 Nilai tinggi (>25%)",
        deal_tier_good: "✨ Hemat (15-25%)",
        filter_search_placeholder: "Cari nama properti atau area...",
        sort_default: "Urutkan listing",
        sort_price_asc: "Harga sewa: Termurah → Termahal",
        sort_price_desc: "Harga sewa: Termahal → Termurah",
        sort_deal_desc: "Skor hemat: Terbesar dahulu",
        sort_m2_asc: "Tarif/m²: Termurah dahulu",
        sort_size_desc: "Luas unit: Terbesar dahulu",
        filter_city_label: "Wilayah kota",
        filter_city_all: "Semua 10 kota & kabupaten",
        filter_subdistrict_label: "Kecamatan atau distrik",
        filter_subdistrict_all: "Semua distrik di kota ini",
        filter_layout_label: "Tipe kamar tidur",
        filter_layout_all: "Semua tipe kamar",
        filter_budget_label: "Batas anggaran bulanan:",
        budget_no_limit: "Semua anggaran (tanpa batas)",
        filter_furnished_label: "Hanya unit full furnished",
        btn_reset_filters: "Reset filter ↺",

        // Tab 1: Districts & Listings
        districts_title: "Distrik & kawasan strategis",
        districts_sub: "Ringkasan tarif median dan unit hemat per kecamatan",
        listings_title: "Daftar listing sewa aktif",
        listings_sub: "Kawasan Jabodetabek",
        showing_units: "Menampilkan {visible} dari {total} unit",
        load_more: "Muat lebih banyak (+30 unit) ↓",
        no_listings_found: "Tidak ada unit yang cocok dengan kriteria filter.",
        no_districts_found: "Tidak ada distrik yang cocok dengan kriteria filter.",
        card_asking_rent: "Harga sewa",
        card_fair_est: "Estimasi wajar",
        card_savings: "Hemat",
        card_view_listing: "Lihat listing",
        deal_deep_badge: "🔥 Nilai tinggi",
        deal_good_badge: "✨ Hemat",
        per_month: "/ bln",
        per_m2: "/m²",
        units_count: "unit",
        districts_count: "distrik",
        deals_available: "unit hemat",
        with_deals: "dengan unit hemat",
        monitored: "dipantau",

        // Tab 1: Benchmark Table & Advisory
        benchmark_table_title: "Benchmark tarif sewa per m² wilayah",
        th_city: "Wilayah",
        th_sample: "Sampel unit",
        th_median_rent: "Median sewa",
        th_rate_m2: "Tarif / m²",
        advisory_title_1: "Penyewa & komuter (Rian)",
        advisory_desc_1: "Bandingkan harga per m² sebelum nego. Unit di sekitar stasiun KRL/MRT umumnya memiliki likuiditas lebih stabil.",
        advisory_title_2: "Negosiasi berbasis data",
        advisory_desc_2: "Gunakan rentang toleransi model AVM kami untuk mengetahui batas wajar penawaran pemilik unit.",
        advisory_title_3: "Fasilitas & perabot",
        advisory_desc_3: "Fit-out full furnished memberi premi tarif sewa 10-18% dibanding unit kosongan (unfurnished).",
        advisory_title_4: "Gradien jarak CBD",
        advisory_desc_4: "Setiap kenaikan 5 km menjauhi Sudirman CBD rata-rata menurunkan tarif sewa sebesar ~12.4% per m².",

        // Tab 2: Simulator
        sim_header_title: "02 // Simulator valuasi sewa pintar",
        sim_header_sub: "Automated Valuation Model (AVM) berbasis regresi spasial & atribut hedonik 728 unit Jabodetabek.",
        sim_spec_title: "Spesifikasi unit & atribut fisik",
        sim_city_label: "Wilayah kota",
        sim_subdistrict_label: "Target kecamatan atau distrik",
        sim_subdistrict_default: "Semua distrik (median kota)",
        sim_size_label: "Luas bangunan bersih (m²)",
        sim_furnish_label: "Kondisi perabot interior",
        sim_furnish_un: "Kosongan (unfurnished)",
        sim_furnish_full: "Lengkap (full furnished)",
        sim_beds_label: "Jumlah kamar tidur",
        sim_baths_label: "Jumlah kamar mandi",
        sim_cbd_label: "Jarak ke Sudirman CBD (km)",
        sim_transit_label: "Jarak ke stasiun transit terdekat (km)",
        sim_amenities_title: "Fasilitas unit tambahan (opsional)",
        sim_amenity_ff: "Interior full furnished",
        sim_amenity_ac: "Air Conditioner (AC)",
        sim_amenity_pool: "Kolam renang apartemen",
        sim_amenity_gym: "Pusat kebugaran (fitness/gym)",
        sim_amenity_balcony: "Balkon privat",
        sim_amenity_kitchen: "Kitchen set lengkap",
        sim_result_title: "Estimasi harga sewa wajar pasar",
        sim_ci_label: "Rentang toleransi pasar:",
        sim_rate_label: "Tarif efektif ruang:",
        sim_advice_title: "Panduan negosiasi penyewa:",
        sim_advice_1: "Jika harga penawaran pemilik di atas rentang batas atas, tanyakan justifikasi interior atau ajukan penawaran di angka estimasi wajar.",
        sim_advice_2: "Jika sewa tahunan dibayar di muka sekaligus, mintalah diskon tambahan 8% - 12% dari estimasi wajar.",
        sim_commuter_insight: "Unit hunian dalam radius <1.5 km dari simpul transit rel (KRL/MRT/LRT) secara konsisten memiliki stabilitas okupansi 15% lebih tinggi.",

        // Tab 3: Pro Investor Portal
        inv_locked_eyebrow: "Akses terbatas // Persona pro",
        inv_locked_title: "Portal eksklusif investor & pemilik properti",
        inv_locked_desc: "Halaman ini dikhususkan bagi pemilik unit dan investor (persona Bu Sarah) untuk menghitung potensi keuntungan sewa, masa balik modal renovasi interior, dan analisis data pasar spasial.",
        inv_locked_btn_demo: "Beralih ke mode investor (demo Bu Sarah)",
        inv_locked_btn_return: "Kembali ke radar pasar",
        inv_unlocked_eyebrow: "Alokasi modal // Analisis yield pro",
        inv_unlocked_title: "03 // Portal investor & analisis imbal hasil (Bu Sarah)",
        inv_unlocked_desc: "Dasbor evaluasi investasi properti sewa, simulasi payback period interior fit-out, dan pemodelan sebaran spasial.",
        inv_signout_btn: "Keluar mode pro",
        fitout_title: "Analisis payback renovasi interior (fit-out)",
        fitout_badge_prefix: "Premi furnished",
        fitout_desc: "Hitung apakah renovasi unit menjadi full furnished sepadan dengan biaya modal yang dikeluarkan dibandingkan dibiarkan kosongan (unfurnished).",
        fitout_kpi_monthly: "Tambahan sewa per bulan",
        fitout_kpi_monthly_sub: "Selisih vs kosongan",
        fitout_kpi_annual: "Tambahan omset per tahun",
        fitout_kpi_annual_sub: "Arus kas tambahan",
        fitout_kpi_cost: "Estimasi modal renovasi",
        fitout_kpi_cost_sub: "Standar renovasi unit 45 m²",
        fitout_kpi_bep: "Masa balik modal (BEP)",
        fitout_kpi_bep_sub: "Estimasi titik impas",
        decay_chart_title: "Gradien penurunan tarif vs jarak ke Sudirman CBD",
        decay_chart_sub: "Model Alonso-Muth-Mills",
        decay_chart_label: "Tarif sewa (Rp/m² vs jarak CBD)",
        decay_x_title: "Jarak ke Sudirman CBD (km)",
        decay_y_title: "Tarif per m² (Rp)",
        zones_title: "Imbal hasil per ring wilayah konsentris",
        zones_sub: "Zonasi konsentris perkotaan",
        th_zone: "Ring perkotaan",
        th_inventory: "Sampel unit",
        th_zone_median: "Median Rp/m²",
        th_zone_mean: "Rata-rata Rp/m²",
        telemetry_title: "Telemetri model valuasi otomatis (AVM)",
        telemetry_r2_label: "R² out-of-fold",
        telemetry_mae_label: "Rata-rata margin error (MAE)",
        telemetry_mape_label: "Error persentase wajar (MAPE)",
        telemetry_top_label: "Fitur paling berpengaruh (GB)",

        // Modal Login
        modal_title: "Masuk ke Household Intelligence",
        modal_desc: "Pilih profil akses yang sesuai dengan tujuan kamu menggunakan platform ini.",
        persona_renter_title: "🔍 Pencari hunian sewa (Rian)",
        persona_renter_badge: "Gratis",
        persona_renter_desc: "Cari unit apartemen murah dekat stasiun, cek kewajaran harga sewa, dan filter unit terbaik di 10 kota Jabodetabek.",
        persona_investor_title: "🏢 Pemilik properti & investor (Bu Sarah)",
        persona_investor_badge: "Akses pro",
        persona_investor_desc: "Akses kalkulator balik modal renovasi interior (fit-out), analisis tarif sewa per meter, dan data statistik ekonometrika.",
        modal_btn_continue: "Lanjutkan ke platform ↗",
        modal_btn_cancel: "Batal",

        // Footer
        footer_left: "HOUSEHOLD INTELLIGENCE // PANDUAN SEWA PROPERTI JABODETABEK",
        footer_right: "AFIATTA ILHAN SALEH • ANALITIK DATA & HEDONIC PRICING"
    },

    en: {
        // Brand & Topbar
        brand_tagline: "// Greater Jakarta rental guide & property intelligence",
        topbar_status_active: "Active units tracked",
        topbar_login_full: "Sign in / Pro investor access",
        topbar_login_mobile: "Pro access",
        topbar_signout: "Sign out",
        topbar_active_profile: "Active profile:",
        investor_pro: "pro investor",

        // Metric Ribbon
        kpi_units_label: "Total units monitored",
        kpi_units_delta: "Across 10 Greater Jakarta regions",
        kpi_rent_label: "Median monthly rent",
        kpi_rent_delta: "Live market benchmark",
        kpi_m2_label: "Median rate per m²",
        kpi_m2_delta: "Effective space rate",
        kpi_bargains_label: "Detected bargain deals",
        kpi_bargains_delta: "Below hedonic market estimate",

        // Tab Navigation
        tab_map: "01 // Rental market & deal explorer",
        tab_simulator: "02 // Smart rent valuation simulator",
        tab_investor: "03 // Pro investor portal (Bu Sarah)",
        badge_locked: "Pro",
        badge_unlocked: "Open",

        // Tab 1: Filters & Explorer
        filter_mode_label: "Feed mode:",
        filter_mode_all: "All active units",
        filter_mode_deals: "⚡ Bargain deal radar",
        deal_tier_all: "All deals",
        deal_tier_deep: "🔥 Deep value (>25%)",
        deal_tier_good: "✨ Good deal (15-25%)",
        filter_search_placeholder: "Search property name or subdistrict...",
        sort_default: "Sort listings",
        sort_price_asc: "Rental price: Low to High",
        sort_price_desc: "Rental price: High to Low",
        sort_deal_desc: "Bargain score: Highest first",
        sort_m2_asc: "Rate / m²: Lowest first",
        sort_size_desc: "Unit size: Largest first",
        filter_city_label: "City / Region",
        filter_city_all: "All 10 cities & regencies",
        filter_subdistrict_label: "Subdistrict or district",
        filter_subdistrict_all: "All districts in this city",
        filter_layout_label: "Bedroom configuration",
        filter_layout_all: "All bedroom types",
        filter_budget_label: "Monthly budget ceiling:",
        budget_no_limit: "All budgets (no limit)",
        filter_furnished_label: "Full furnished units only",
        btn_reset_filters: "Reset filters ↺",

        // Tab 1: Districts & Listings
        districts_title: "Strategic districts & hubs",
        districts_sub: "Median rate summary and bargain counts per subdistrict",
        listings_title: "Active rental listings",
        listings_sub: "Greater Jakarta Area",
        showing_units: "Showing {visible} of {total} units",
        load_more: "Load more (+30 units) ↓",
        no_listings_found: "No listings match the selected filter criteria.",
        no_districts_found: "No districts match the selected filter criteria.",
        card_asking_rent: "Asking rent",
        card_fair_est: "Fair estimate",
        card_savings: "Savings",
        card_view_listing: "View listing",
        deal_deep_badge: "🔥 Deep value",
        deal_good_badge: "✨ Good deal",
        per_month: "/ mo",
        per_m2: "/m²",
        units_count: "units",
        districts_count: "districts",
        deals_available: "deals available",
        with_deals: "with deals",
        monitored: "monitored",

        // Tab 1: Benchmark Table & Advisory
        benchmark_table_title: "Regional rental rate benchmark per m²",
        th_city: "Region",
        th_sample: "Sample units",
        th_median_rent: "Median rent",
        th_rate_m2: "Rate / m²",
        advisory_title_1: "Tenants & commuters (Rian)",
        advisory_desc_1: "Compare rate per m² before negotiating. Units adjacent to commuter rail / MRT stations generally sustain higher occupancy.",
        advisory_title_2: "Data-backed negotiation",
        advisory_desc_2: "Use our AVM tolerance interval to establish reasonable counter-offer boundaries with landlords.",
        advisory_title_3: "Amenities & interior fit-out",
        advisory_desc_3: "Full furnished interior delivers a 10-18% rental rate premium over unfurnished units.",
        advisory_title_4: "CBD distance decay",
        advisory_desc_4: "Every 5 km farther from Sudirman CBD reduces effective rental rate by ~12.4% per m² on average.",

        // Tab 2: Simulator
        sim_header_title: "02 // Smart rent valuation simulator",
        sim_header_sub: "Automated Valuation Model (AVM) based on spatial regression & hedonic pricing across 728 Jabodetabek units.",
        sim_spec_title: "Unit specifications & physical attributes",
        sim_city_label: "City / Region",
        sim_subdistrict_label: "Target subdistrict or district",
        sim_subdistrict_default: "All districts (city median)",
        sim_size_label: "Net floor area (m²)",
        sim_furnish_label: "Interior furnishing condition",
        sim_furnish_un: "Unfurnished",
        sim_furnish_full: "Full furnished",
        sim_beds_label: "Bedrooms",
        sim_baths_label: "Bathrooms",
        sim_cbd_label: "Distance to Sudirman CBD (km)",
        sim_transit_label: "Distance to nearest rail transit (km)",
        sim_amenities_title: "Additional unit amenities (optional)",
        sim_amenity_ff: "Full furnished interior",
        sim_amenity_ac: "Air conditioning (AC)",
        sim_amenity_pool: "Swimming pool access",
        sim_amenity_gym: "Fitness center / Gym",
        sim_amenity_balcony: "Private balcony",
        sim_amenity_kitchen: "Fitted kitchen set",
        sim_result_title: "Estimated fair market rent",
        sim_ci_label: "Market tolerance range:",
        sim_rate_label: "Effective space rate:",
        sim_advice_title: "Tenant negotiation advice:",
        sim_advice_1: "If the landlord asks above the upper tolerance band, request interior justification or bid at fair market estimate.",
        sim_advice_2: "When paying an entire annual lease upfront, request an additional 8% - 12% discount from fair estimate.",
        sim_commuter_insight: "Units located within <1.5 km of transit hubs (KRL/MRT/LRT) consistently exhibit 15% higher occupancy stability.",

        // Tab 3: Pro Investor Portal
        inv_locked_eyebrow: "Restricted access // Pro persona",
        inv_locked_title: "Exclusive portal for investors & property owners",
        inv_locked_desc: "This dashboard is designed for unit owners and property investors (Bu Sarah persona) to calculate rental yields, interior renovation payback periods, and spatial market data.",
        inv_locked_btn_demo: "Switch to investor mode (demo Bu Sarah)",
        inv_locked_btn_return: "Return to market radar",
        inv_unlocked_eyebrow: "Capital allocation // Pro yield analytics",
        inv_unlocked_title: "03 // Pro investor portal & yield analysis (Bu Sarah)",
        inv_unlocked_desc: "Investment evaluation dashboard for rental properties, interior fit-out payback simulations, and spatial rent gradient modeling.",
        inv_signout_btn: "Sign out pro mode",
        fitout_title: "Interior fit-out payback & ROI analysis",
        fitout_badge_prefix: "Furnished premium",
        fitout_desc: "Calculate whether upgrading a unit to full furnished is worth the capital expenditure compared to leaving it unfurnished.",
        fitout_kpi_monthly: "Monthly rental uplift",
        fitout_kpi_monthly_sub: "Difference vs unfurnished",
        fitout_kpi_annual: "Annual revenue uplift",
        fitout_kpi_annual_sub: "Additional cashflow",
        fitout_kpi_cost: "Est. fit-out capital",
        fitout_kpi_cost_sub: "Standard 45 m² unit fit-out",
        fitout_kpi_bep: "Payback period (BEP)",
        fitout_kpi_bep_sub: "Break-even estimate",
        decay_chart_title: "Rental rate decay gradient vs distance to Sudirman CBD",
        decay_chart_sub: "Alonso-Muth-Mills Model",
        decay_chart_label: "Rental rate (Rp/m² vs CBD distance)",
        decay_x_title: "Distance to Sudirman CBD (km)",
        decay_y_title: "Rate per m² (Rp)",
        zones_title: "Yield & rates across concentric urban rings",
        zones_sub: "Urban concentric zoning",
        th_zone: "Urban ring",
        th_inventory: "Sample units",
        th_zone_median: "Median Rp/m²",
        th_zone_mean: "Mean Rp/m²",
        telemetry_title: "Automated Valuation Model (AVM) telemetry",
        telemetry_r2_label: "Out-of-fold R²",
        telemetry_mae_label: "Mean Absolute Error (MAE)",
        telemetry_mape_label: "Fair percentage error (MAPE)",
        telemetry_top_label: "Most influential feature (GB)",

        // Modal Login
        modal_title: "Sign in to Household Intelligence",
        modal_desc: "Choose an access persona tailored to your objective on this platform.",
        persona_renter_title: "🔍 Public Tenant & Commuter (Rian)",
        persona_renter_badge: "Free",
        persona_renter_desc: "Find affordable apartments near transit, check fair rental prices, and compare units across 10 Greater Jakarta cities.",
        persona_investor_title: "🏢 Property Owner & Investor (Bu Sarah)",
        persona_investor_badge: "Pro access",
        persona_investor_desc: "Access interior fit-out payback calculators, spatial rate per m² decay models, and econometric statistics.",
        modal_btn_continue: "Continue to platform ↗",
        modal_btn_cancel: "Cancel",

        // Footer
        footer_left: "HOUSEHOLD INTELLIGENCE // GREATER JAKARTA PROPERTY RENTAL GUIDE",
        footer_right: "AFIATTA ILHAN SALEH • DATA ANALYTICS & HEDONIC PRICING"
    }
};

/**
 * Returns translated string for a given key, with fallback.
 */
function t(key, fallback = '') {
    const lang = (window.AppState && window.AppState.currentLanguage) || 'id';
    const dict = I18N_DICTIONARY[lang] || I18N_DICTIONARY.id;
    return dict[key] !== undefined ? dict[key] : (fallback || key);
}
window.t = t;

/**
 * Applies language across all static data-i18n elements and updates dynamic state.
 */
function setLanguage(lang) {
    if (lang !== 'id' && lang !== 'en') lang = 'id';
    
    if (window.AppState) {
        window.AppState.currentLanguage = lang;
    }
    localStorage.setItem('hi_lang', lang);
    document.documentElement.setAttribute('lang', lang);

    // Update active button state
    const btnId = document.getElementById('lang-btn-id');
    const btnEn = document.getElementById('lang-btn-en');
    if (btnId) btnId.classList.toggle('active', lang === 'id');
    if (btnEn) btnEn.classList.toggle('active', lang === 'en');

    // Translate DOM elements with data-i18n
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (key) {
            const translation = t(key);
            if (translation) {
                // If element has bubble icon or child tags, preserve them if needed
                const bubble = el.querySelector('.btn-bubble-icon');
                if (bubble) {
                    const textSpan = el.querySelector('span:first-child');
                    if (textSpan) {
                        textSpan.innerText = translation;
                    } else {
                        el.childNodes[0].nodeValue = translation + ' ';
                    }
                } else {
                    el.innerText = translation;
                }
            }
        }
    });

    // Translate inputs with data-i18n-placeholder
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (key) {
            el.setAttribute('placeholder', t(key));
        }
    });

    // Update dynamic subdistrict placeholder in Simulator
    const simSubSel = document.getElementById('sim-subdistrict');
    if (simSubSel && simSubSel.options.length > 0) {
        simSubSel.options[0].text = t('sim_subdistrict_default');
    }

    // Refresh dynamic views if functions are available
    if (typeof window.applyFilters === 'function') {
        window.applyFilters();
    }
    if (typeof window.renderDistrictsGrid === 'function') {
        window.renderDistrictsGrid();
    }
    if (typeof window.runSimulation === 'function') {
        window.runSimulation();
    }
    if (typeof window.updateBudgetLabel === 'function') {
        const budgetInput = document.getElementById('filter-budget');
        if (budgetInput) window.updateBudgetLabel(budgetInput.value);
    }
    if (window.AppState && window.AppState.lastTelemetryData && typeof window.updateTelemetryUI === 'function') {
        window.updateTelemetryUI(window.AppState.lastTelemetryData);
    }
    if (window.AppState && window.AppState.decayData && typeof window.renderZonesTable === 'function') {
        window.renderZonesTable(window.AppState.decayData.zones);
    }
    if (window.AppState && window.AppState.decayData && typeof window.renderDecayChart === 'function') {
        window.renderDecayChart(window.AppState.decayData.points);
    }
}
window.setLanguage = setLanguage;

