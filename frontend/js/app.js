/**
 * app.js
 * Main Application Lifecycle, Coordinator, & Entry Point
 */

async function initApp() {
    try {
        const [telemetry, benchmarks, districts, listings, decay] = await Promise.all([
            API.fetchTelemetry(),
            API.fetchBenchmarks(),
            API.fetchDistricts(),
            API.fetchListings(),
            API.fetchDistanceDecay()
        ]);

        if (telemetry) {
            updateTelemetryUI(telemetry);
        }
        if (benchmarks && benchmarks.cities) {
            AppState.allBenchmarks = benchmarks;
            renderBenchmarkTable(benchmarks.cities);
        }
        if (districts && districts.districts) {
            AppState.allDistricts = districts.districts;
            populateFilterSubdistricts();
            renderDistrictsGrid();
        }
        if (listings) {
            AppState.allListings = listings.data || listings.listings || [];
            applyFilters();
        }
        if (decay) {
            AppState.decayData = decay;
            renderDecayChart(decay.points);
            renderZonesTable(decay.zones);
        }
    } catch (err) {
        console.error("Initialization error:", err);
    }

    updateSimSubdistricts();
    runSimulation();

    // Initialize Theme & Language
    if (typeof initTheme === 'function') {
        initTheme();
    }
    if (typeof setLanguage === 'function') {
        setLanguage(AppState.currentLanguage || 'id');
    }

    // Check localStorage auth state
    const savedRole = localStorage.getItem('hi_user_role');
    if (savedRole === 'investor') {
        setInvestorRole(true);
    }
}
window.initApp = initApp;

function updateTelemetryUI(data) {
    if (!data) return;
    if (window.AppState) {
        window.AppState.lastTelemetryData = data;
    }

    const isEn = (AppState.currentLanguage === 'en');
    const unitWord = typeof t === 'function' ? t('units_count', 'unit') : 'unit';
    const jtWord = isEn ? 'M' : 'jt';
    const rbWord = isEn ? 'k' : 'rb';

    if (document.getElementById('kpi-units')) {
        document.getElementById('kpi-units').innerText = (data.audited_units || 728).toLocaleString() + ' ' + unitWord;
    }
    if (document.getElementById('kpi-rent') && data.median_rent_idr) {
        document.getElementById('kpi-rent').innerText = 'Rp ' + (data.median_rent_idr / 1e6).toFixed(1) + ' ' + jtWord;
    }
    if (document.getElementById('kpi-m2') && data.median_price_per_m2_idr) {
        document.getElementById('kpi-m2').innerText = 'Rp ' + Math.round(data.median_price_per_m2_idr / 1000) + ' ' + rbWord;
    }
    if (document.getElementById('kpi-bargains')) {
        const count = data.bargains_detected !== undefined ? data.bargains_detected : (data.deals ? data.deals.below_estimate_total : 139);
        document.getElementById('kpi-bargains').innerText = count + ' ' + unitWord;
    }
    if (document.getElementById('topbar-status-text')) {
        document.getElementById('topbar-status-text').innerText = (data.audited_units || 728).toLocaleString() + ' ' + (isEn ? 'active units monitored' : 'unit aktif dipantau');
    }
    if (document.getElementById('count-all-badge')) {
        document.getElementById('count-all-badge').innerText = (data.audited_units || 728).toLocaleString();
    }
    if (document.getElementById('count-deals-badge')) {
        const count = data.bargains_detected !== undefined ? data.bargains_detected : 139;
        document.getElementById('count-deals-badge').innerText = count.toLocaleString();
    }
    if (document.getElementById('badge-furnish-premium')) {
        const prem = typeof data.furnishing_premium_adjusted_pct === 'number' ? data.furnishing_premium_adjusted_pct : 13.9;
        const prefix = isEn ? 'Furnished premium +' : 'Premi furnished +';
        document.getElementById('badge-furnish-premium').innerText = prefix + prem + '%';
    }
    const m = data.model;
    if (m) {
        const fname = (f) => {
            if (isEn) {
                return ({ log_floor_size: 'Floor area', distance_to_cbd_km: 'Distance to CBD', distance_to_transit_km: 'Distance to transit', bedrooms: 'Bedrooms', bathrooms: 'Bathrooms', is_full_furnished: 'Full furnished' }[f] || f.replace('city_', 'City: '));
            }
            return ({ log_floor_size: 'Luas bangunan', distance_to_cbd_km: 'Jarak ke CBD', distance_to_transit_km: 'Jarak ke transit', bedrooms: 'Kamar tidur', bathrooms: 'Kamar mandi', is_full_furnished: 'Perabot lengkap' }[f] || f.replace('city_', 'Kota: '));
        };
        if (document.getElementById('avm-badge')) document.getElementById('avm-badge').innerText = 'R² out-of-fold = ' + (m.r2 * 100).toFixed(1) + '%';
        if (document.getElementById('avm-r2')) document.getElementById('avm-r2').innerText = (m.r2 * 100).toFixed(1) + '% R²';
        const baselinePrefix = isEn ? 'Naive baseline ' : 'Baseline naif ';
        const unseenWord = isEn ? ' · unseen subdistricts ' : ' · distrik baru ';
        if (document.getElementById('avm-r2-sub')) document.getElementById('avm-r2-sub').innerText = baselinePrefix + (m.baseline_naive_r2 * 100).toFixed(1) + '%' + unseenWord + (m.unseen_subdistrict_r2 * 100).toFixed(1) + '%';
        if (document.getElementById('avm-mae')) document.getElementById('avm-mae').innerText = 'Rp ' + (m.mae_idr / 1e6).toFixed(2) + ' ' + jtWord;
        if (document.getElementById('avm-mape')) document.getElementById('avm-mape').innerText = m.mape_pct.toFixed(1) + '% MAPE';
        const typicalListing = isEn ? '(typical listing)' : '(unit tipikal)';
        if (document.getElementById('avm-mape-sub')) document.getElementById('avm-mape-sub').innerText = 'Median APE ' + m.median_ape_pct.toFixed(1) + '% ' + typicalListing;
        if (m.top_features && m.top_features.length >= 2) {
            const thenWord = isEn ? 'Then ' : 'Lalu ';
            if (document.getElementById('avm-f1')) document.getElementById('avm-f1').innerText = fname(m.top_features[0].feature) + ' (' + (m.top_features[0].importance * 100).toFixed(1) + '%)';
            if (document.getElementById('avm-f2')) document.getElementById('avm-f2').innerText = thenWord + fname(m.top_features[1].feature) + ' (' + (m.top_features[1].importance * 100).toFixed(1) + '%)';
        }
    }
}

function switchTab(tabId) {
    if (tabId === 'tab-deals') {
        tabId = 'tab-map';
        setInventoryMode('deals');
    }
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));

    const targetEl = document.getElementById(tabId);
    if (targetEl) targetEl.classList.add('active');

    if (tabId === 'tab-map') {
        const btn = document.getElementById('tab-btn-map');
        if (btn) btn.classList.add('active');
    } else if (tabId === 'tab-simulator') {
        const btn = document.getElementById('tab-btn-simulator');
        if (btn) btn.classList.add('active');
    } else if (tabId === 'tab-investor') {
        const btn = document.getElementById('tab-btn-investor');
        if (btn) btn.classList.add('active');
        if (AppState.decayChartInstance) {
            setTimeout(() => AppState.decayChartInstance.resize(), 50);
        }
    }
}
window.switchTab = switchTab;

function updateBudgetLabel(val) {
    const num = parseFloat(val);
    const label = document.getElementById('budget-label');
    if (!label) return;
    const isEn = (AppState.currentLanguage === 'en');
    if (num >= 100000000) {
        label.innerText = typeof t === 'function' ? t('budget_no_limit', 'Semua anggaran (tanpa batas)') : 'Semua anggaran (tanpa batas)';
    } else {
        const jt = (num / 1e6).toFixed(1);
        const perMonth = typeof t === 'function' ? t('per_month', '/ bln') : '/ bln';
        const jtWord = isEn ? 'M' : 'jt';
        label.innerText = isEn ? `Max Rp ${jt} ${jtWord} ${perMonth}` : `Maks Rp ${jt} ${jtWord} ${perMonth}`;
    }
}
window.updateBudgetLabel = updateBudgetLabel;

// Launch application on DOM ready
window.addEventListener('DOMContentLoaded', initApp);

