/**
 * app.js
 * Main Application Lifecycle, Coordinator, & Entry Point
 */

/**
 * Kegagalan API dulu SENYAP: api.js menelan error lalu UI menampilkan angka
 * fallback yang terlihat seperti data asli. Sekarang setiap kegagalan dicatat
 * dan ditampilkan sebagai banner, supaya user tahu datanya tidak lengkap.
 */
function reportApiFailure(endpoint, err) {
    const failures = window.__apiFailures || (window.__apiFailures = []);
    if (!failures.some(f => f.endpoint === endpoint)) {
        failures.push({ endpoint: endpoint, message: (err && err.message) ? err.message : 'gagal' });
    }
    renderDataErrorBanner();
}
window.reportApiFailure = reportApiFailure;

function clearApiFailure(endpoint) {
    const current = window.__apiFailures;
    if (!current) return;
    const remaining = current.filter(f => f.endpoint !== endpoint);
    if (remaining.length === current.length) return;
    window.__apiFailures = remaining;

    const banner = document.getElementById('data-error-banner');
    if (remaining.length === 0) {
        if (banner) banner.remove();
    } else {
        renderDataErrorBanner();
    }
}
window.clearApiFailure = clearApiFailure;

function renderDataErrorBanner() {
    const failures = window.__apiFailures || [];
    if (!failures.length) return;

    let banner = document.getElementById('data-error-banner');
    if (!banner) {
        banner = document.createElement('div');
        banner.id = 'data-error-banner';
        banner.setAttribute('role', 'alert');
        banner.style.cssText = 'position:fixed;left:0;right:0;bottom:0;z-index:9999;background:#b3261e;color:#fff;padding:10px 16px;font-size:12px;display:flex;gap:12px;align-items:center;justify-content:center;flex-wrap:wrap;';
        document.body.appendChild(banner);
    }

    const isEn = (typeof AppState !== 'undefined' && AppState.currentLanguage === 'en');
    const list = failures.map(f => f.endpoint).join(', ');
    banner.innerHTML = '';

    const text = document.createElement('span');
    text.innerText = isEn
        ? `Could not load: ${list}. Some figures may be missing.`
        : `Gagal memuat: ${list}. Sebagian angka mungkin tidak lengkap.`;

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.innerText = isEn ? 'Reload' : 'Muat ulang';
    btn.style.cssText = 'background:#fff;color:#b3261e;border:0;border-radius:4px;padding:4px 12px;font-weight:600;cursor:pointer;font-size:12px;';
    btn.onclick = function () { location.reload(); };

    banner.appendChild(text);
    banner.appendChild(btn);
}
window.renderDataErrorBanner = renderDataErrorBanner;

/**
 * Keadaan saat data sedang dimuat. Dulu tidak ada: selama fetch berjalan halaman
 * menampilkan "Menampilkan 0 dari 0 unit" dan badge distrik 100 (angka hardcode),
 * sehingga terlihat seperti hasil pencarian yang kosong.
 */
function renderListingsLoading() {
    const container = document.getElementById('tab1-listings-container');
    const status = document.getElementById('pagination-status');
    const btnLoadMore = document.getElementById('btn-load-more');
    const isEn = (typeof AppState !== 'undefined' && AppState.currentLanguage === 'en');
    if (container && !container.dataset.loaded) {
        container.innerHTML = `<div class="mono" style="color: var(--color-fog); padding: 36px; text-align: center; font-size: 12px; grid-column: 1 / -1;">`
            + (isEn ? 'Loading listing data…' : 'Memuat data unit…') + `</div>`;
    }
    if (status) status.innerText = isEn ? 'Loading…' : 'Memuat data…';
    if (btnLoadMore) btnLoadMore.style.display = 'none';
}
window.renderListingsLoading = renderListingsLoading;

/**
 * Daftar unit tidak bisa dimuat: bedakan dari "filter tidak menemukan apa-apa".
 * Dulu kondisi ini tampil sebagai "Menampilkan 0 dari 0 unit" seolah pencariannya kosong.
 */
function renderListingsUnavailable() {
    const container = document.getElementById('tab1-listings-container');
    const status = document.getElementById('pagination-status');
    const btnLoadMore = document.getElementById('btn-load-more');
    const isEn = (typeof AppState !== 'undefined' && AppState.currentLanguage === 'en');
    if (container) {
        container.dataset.loaded = 'failed';
        container.innerHTML = `<div style="color: var(--color-fog); padding: 36px; text-align: center; font-size: 13px; grid-column: 1 / -1;">`
            + (isEn ? 'Could not load the listing catalog from the server.'
                    : 'Gagal memuat katalog unit dari server.') + `</div>`;
    }
    if (status) status.innerText = isEn ? 'No data loaded' : 'Data belum termuat';
    if (btnLoadMore) btnLoadMore.style.display = 'none';
}
window.renderListingsUnavailable = renderListingsUnavailable;

async function initApp() {
    // Tampilkan keadaan memuat lebih dulu supaya halaman tidak terlihat seperti
    // pencarian kosong selama fetch 2 MB berjalan.
    renderListingsLoading();
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
        if (listings && (listings.data || listings.listings)) {
            AppState.allListings = listings.data || listings.listings;
            applyFilters();
        } else {
            // Bedakan "gagal memuat data" dari "filter tidak menemukan apa-apa".
            renderListingsUnavailable();
        }
        if (decay) {
            AppState.decayData = decay;
            renderDecayChart(decay.points);
            renderZonesTable(decay.zones);
        }
    } catch (err) {
        console.error("Initialization error:", err);
        reportApiFailure('initialization', err);
        renderListingsUnavailable();
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
        // Ambang deal datang dari server (src/deal_config.py). Frontend tidak lagi
        // punya angka sendiri.
        if (data.deal_thresholds && typeof data.deal_thresholds.good_z === 'number') {
            window.AppState.dealThresholds = {
                good_z: data.deal_thresholds.good_z,
                deep_z: data.deal_thresholds.deep_z
            };
        }
    }

    const isEn = (AppState.currentLanguage === 'en');
    const unitWord = typeof t === 'function' ? t('units_count', 'unit') : 'unit';
    const jtWord = isEn ? 'M' : 'jt';
    const rbWord = isEn ? 'k' : 'rb';

    // Jangan pernah menampilkan angka karangan. Kalau field tidak ada dari API,
    // tampilkan '—' supaya jelas datanya belum termuat. Sebelumnya baris-baris di
    // bawah ini punya fallback 728 unit / 139 deal / 13.9% yang tampil seolah
    // data asli ketika request gagal.
    const MISSING = '—';
    const numOr = (value, fmt) => (typeof value === 'number' && isFinite(value)) ? fmt(value) : MISSING;

    if (document.getElementById('kpi-units')) {
        document.getElementById('kpi-units').innerText = numOr(data.audited_units, v => v.toLocaleString('id-ID') + ' ' + unitWord);
    }
    if (document.getElementById('kpi-rent')) {
        document.getElementById('kpi-rent').innerText = numOr(data.median_rent_idr, v => 'Rp ' + (v / 1e6).toFixed(1) + ' ' + jtWord);
    }
    if (document.getElementById('kpi-m2')) {
        document.getElementById('kpi-m2').innerText = numOr(data.median_price_per_m2_idr, v => 'Rp ' + Math.round(v / 1000) + ' ' + rbWord);
    }
    if (document.getElementById('kpi-bargains')) {
        document.getElementById('kpi-bargains').innerText = numOr(data.bargains_detected, v => v + ' ' + unitWord);
    }
    if (document.getElementById('topbar-status-text')) {
        document.getElementById('topbar-status-text').innerText = numOr(
            data.audited_units,
            v => v.toLocaleString('id-ID') + ' ' + (isEn ? 'active units monitored' : 'unit aktif dipantau')
        );
    }
    if (document.getElementById('count-all-badge')) {
        document.getElementById('count-all-badge').innerText = numOr(data.audited_units, v => v.toLocaleString('id-ID'));
    }
    if (document.getElementById('count-deals-badge')) {
        document.getElementById('count-deals-badge').innerText = numOr(data.bargains_detected, v => v.toLocaleString('id-ID'));
    }
    if (document.getElementById('badge-furnish-premium')) {
        const prefix = isEn ? 'Furnished premium +' : 'Premi furnished +';
        document.getElementById('badge-furnish-premium').innerText = numOr(
            data.furnishing_premium_adjusted_pct,
            v => prefix + v + '%'
        );
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

