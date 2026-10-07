/**
 * explorer.js
 * Tab 1: Rental Market & Deal Explorer Logic
 */

function setInventoryMode(mode) {
    AppState.currentInventoryMode = mode;
    const btnAll = document.getElementById('mode-btn-all');
    const btnDeals = document.getElementById('mode-btn-deals');
    const tierFilters = document.getElementById('deal-tier-filters');

    if (btnAll) btnAll.classList.toggle('active', mode === 'all');
    if (btnDeals) btnDeals.classList.toggle('active', mode === 'deals');
    if (tierFilters) tierFilters.style.display = (mode === 'deals') ? 'flex' : 'none';

    applyFilters();
}
window.setInventoryMode = setInventoryMode;

function setDealTier(tier) {
    AppState.currentDealTier = tier;
    ['all', 'deep', 'good'].forEach(t => {
        const el = document.getElementById('tier-pill-' + t);
        if (el) el.classList.toggle('active', t === tier);
    });
    applyFilters();
}
window.setDealTier = setDealTier;
window.filterDealsTier = setDealTier;

function populateFilterSubdistricts() {
    const city = document.getElementById('filter-city').value;
    const sel = document.getElementById('filter-subdistrict');
    if (!sel) return;
    const currentVal = sel.value;
    const defaultLabel = typeof t === 'function' ? t('filter_subdistrict_all', 'Semua distrik di kota ini') : 'Semua distrik di kota ini';
    sel.innerHTML = `<option value="All">${defaultLabel}</option>`;

    const unitWord = typeof t === 'function' ? t('units_count', 'unit') : 'unit';
    const matched = AppState.allDistricts.filter(d => city === 'All' || d.target_city === city);
    matched.forEach(d => {
        const opt = document.createElement('option');
        opt.value = d.subdistrict;
        opt.innerText = `${d.subdistrict} (${d.unit_count} ${unitWord})`;
        sel.appendChild(opt);
    });
    if (matched.some(d => d.subdistrict === currentVal)) {
        sel.value = currentVal;
    }
}
window.populateFilterSubdistricts = populateFilterSubdistricts;

function onCityFilterChange() {
    populateFilterSubdistricts();
    applyFilters();
}
window.onCityFilterChange = onCityFilterChange;

function renderDistrictsGrid() {
    const container = document.getElementById('districts-grid-container');
    const badge = document.getElementById('districts-count-badge');
    if (!container) return;

    const selectedCity = document.getElementById('filter-city').value;
    const subdistrictEl = document.getElementById('filter-subdistrict');
    const selectedSub = subdistrictEl ? subdistrictEl.value : 'All';

    let matched = AppState.allDistricts.filter(d => selectedCity === 'All' || d.target_city === selectedCity);
    if (AppState.currentInventoryMode === 'deals') {
        matched = matched.filter(d => d.deals_count > 0);
    }

    const distWord = typeof t === 'function' ? t('districts_count', 'distrik') : 'distrik';
    const withDealsWord = typeof t === 'function' ? t('with_deals', 'dengan unit hemat') : 'dengan unit hemat';
    const monWord = typeof t === 'function' ? t('monitored', 'dipantau') : 'dipantau';
    const dealsWord = typeof t === 'function' ? t('deals_available', 'unit hemat') : 'unit hemat';
    const perMonth = typeof t === 'function' ? t('per_month', '/ bln') : '/ bln';
    const jtWord = typeof t === 'function' ? t('unit_million', 'jt') : 'jt';
    const rbWord = typeof t === 'function' ? t('unit_thousand', 'rb') : 'rb';
    const perM2 = typeof t === 'function' ? t('per_m2', '/m²') : '/m²';

    if (badge) {
        badge.innerText = `${matched.length} ${distWord} ${AppState.currentInventoryMode === 'deals' ? withDealsWord : monWord}`;
    }

    if (matched.length === 0) {
        container.innerHTML = `<div style="color: var(--color-fog); padding: 16px; font-size: 12px;">${typeof t === 'function' ? t('no_districts_found', 'Tidak ada distrik yang cocok dengan kriteria filter.') : 'Tidak ada distrik yang cocok dengan kriteria filter.'}</div>`;
        return;
    }

    const cardsHtml = matched.map(d => {
        const isActive = (selectedSub !== 'All' && d.subdistrict === selectedSub);
        // Nama kawasan berasal dari scraping: escape untuk teks DAN atribut.
        // Dulu nilainya diinterpolasi mentah ke onclick="..." sehingga kutip atau
        // tag di nama kawasan bisa keluar dari atribut / DOM.
        const subLabel = escapeHtml(d.subdistrict);
        const cityLabel = escapeHtml(d.target_city);
        return `
            <div class="district-card ${isActive ? 'active' : ''}" data-subdistrict="${subLabel}" data-city="${cityLabel}" role="button" tabindex="0">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px;">
                    <div>
                        <div class="mono" style="font-size: 10px; color: var(--color-fog);">${cityLabel}</div>
                        <div style="font-size: 13px; font-weight: 600; color: var(--color-carbon-ink);">${subLabel}</div>
                    </div>
                    <span class="mono" style="font-size: 10px; background: var(--color-newsprint-gray); border: 1px solid var(--color-pebble); padding: 1px 6px; border-radius: 4px; color: var(--color-carbon-ink); font-weight: 500;">${d.unit_count}</span>
                </div>
                <div style="border-top: 1px solid var(--color-pebble); padding-top: 6px; margin-top: 6px; display: flex; justify-content: space-between; align-items: baseline;">
                    <div class="mono" style="font-size: 12px; color: var(--color-carbon-ink); font-weight: 600;">
                        Rp ${(d.median_rent_idr / 1e6).toFixed(1)} ${jtWord} <span style="font-size: 10px; color: var(--color-fog); font-weight: 400;">${perMonth}</span>
                    </div>
                    <div class="mono" style="font-size: 10px; color: var(--color-fog);">
                        Rp ${Math.round(d.median_price_per_m2_idr / 1000)} ${rbWord}${perM2}
                    </div>
                </div>
                ${d.deals_count > 0 ? `<div style="font-size: 10px; color: var(--color-carbon-ink); margin-top: 4px; font-weight: 600;">⚡ ${d.deals_count} ${dealsWord}</div>` : ''}
            </div>
        `;
    }).join('');

    container.innerHTML = cardsHtml;
    // Delegasi event: nama kawasan tidak lagi disisipkan ke atribut onclick=.
    container.onclick = function (ev) {
        const card = ev.target.closest ? ev.target.closest('.district-card') : null;
        if (!card || !container.contains(card)) return;
        selectDistrict(card.dataset.subdistrict, card.dataset.city);
    };
    container.onkeydown = function (ev) {
        if (ev.key !== 'Enter' && ev.key !== ' ') return;
        const card = ev.target.closest ? ev.target.closest('.district-card') : null;
        if (!card) return;
        ev.preventDefault();
        selectDistrict(card.dataset.subdistrict, card.dataset.city);
    };
}
window.renderDistrictsGrid = renderDistrictsGrid;

function selectDistrict(subdistrict, city) {
    const cityEl = document.getElementById('filter-city');
    if (cityEl && cityEl.value !== city && cityEl.value !== 'All') {
        cityEl.value = city;
    }
    populateFilterSubdistricts();
    const subEl = document.getElementById('filter-subdistrict');
    if (subEl) {
        if (subEl.value === subdistrict) {
            subEl.value = 'All';
        } else {
            subEl.value = subdistrict;
        }
    }
    applyFilters();
}
window.selectDistrict = selectDistrict;
window.selectDistrictFromMap = selectDistrict;

function resetAllFilters() {
    document.getElementById('filter-city').value = 'All';
    populateFilterSubdistricts();
    const sub = document.getElementById('filter-subdistrict');
    if (sub) sub.value = 'All';
    document.getElementById('filter-layout').value = 'All';
    document.getElementById('filter-budget').value = 100000000;
    updateBudgetLabel(100000000);
    document.getElementById('filter-furnished').checked = false;
    const searchEl = document.getElementById('filter-search');
    if (searchEl) searchEl.value = '';
    const sortEl = document.getElementById('filter-sort');
    if (sortEl) sortEl.value = 'default';
    AppState.visibleListingsCount = 60;
    setInventoryMode('all');
    setDealTier('all');
    applyFilters();
}
window.resetAllFilters = resetAllFilters;

function onSearchInput() {
    clearTimeout(AppState.searchDebounceTimer);
    AppState.searchDebounceTimer = setTimeout(() => {
        AppState.visibleListingsCount = 60;
        applyFilters();
    }, 200);
}
window.onSearchInput = onSearchInput;

function loadMoreListings() {
    AppState.visibleListingsCount += 30;
    renderListingsCards(AppState.currentFilteredListings);
}
window.loadMoreListings = loadMoreListings;

function applyFilters() {
    const selectedCity = document.getElementById('filter-city').value;
    const subdistrictEl = document.getElementById('filter-subdistrict');
    const selectedSubdistrict = subdistrictEl ? subdistrictEl.value : 'All';
    const selectedLayout = document.getElementById('filter-layout').value;
    const maxBudget = parseFloat(document.getElementById('filter-budget').value);
    const furnishedOnly = document.getElementById('filter-furnished').checked;
    const searchEl = document.getElementById('filter-search');
    const searchQuery = searchEl ? searchEl.value.trim().toLowerCase() : '';
    const sortOrder = document.getElementById('filter-sort') ? document.getElementById('filter-sort').value : 'default';

    let filtered = AppState.allListings.filter(item => {
        if (selectedCity !== 'All' && item.target_city !== selectedCity) return false;
        if (selectedSubdistrict !== 'All' && item.subdistrict !== selectedSubdistrict) return false;
        
        // Robust Layout / Bedroom filtering matching backend data model
        if (selectedLayout !== 'All') {
            const beds = parseInt(item.bedrooms);
            const cat = item.layout_category || '';
            let layoutMatch = false;
            if (selectedLayout === 'Studio') {
                layoutMatch = (beds === 0);
            } else if (selectedLayout === '1BR') {
                layoutMatch = (beds === 1);
            } else if (selectedLayout === '2BR') {
                layoutMatch = (beds === 2);
            } else if (selectedLayout === '3BR') {
                layoutMatch = (beds === 3);
            } else if (selectedLayout === '4BR+') {
                layoutMatch = (beds >= 4);
            } else {
                layoutMatch = (cat === selectedLayout);
            }
            if (!layoutMatch) return false;
        }

        if (maxBudget < 100000000 && item.price_monthly_idr > maxBudget) return false;
        if (furnishedOnly && !item.is_full_furnished) return false;

        if (AppState.currentInventoryMode === 'deals') {
            // Ambang TUNGGAL dari /api/telemetry -> deal_thresholds
            // (sumber: src/deal_config.py). Frontend tidak punya angka sendiri.
            // Sebelumnya baris ini memakai -1.2 + field `deal_tier` yang tidak ada
            // di dataset, sehingga 29 unit salah label "Deep Value".
            const thresholds = AppState.dealThresholds;
            if (!thresholds) {
                // Belum ada ambang dari server -> jangan mengarang klasifikasi.
                // Banner error sudah memberi tahu bahwa data gagal dimuat.
                return false;
            }
            const z = item.deal_score_z;
            if (z > thresholds.good_z) return false;
            if (AppState.currentDealTier === 'deep' && z > thresholds.deep_z) return false;
            if (AppState.currentDealTier === 'good' && z <= thresholds.deep_z) return false;
        }

        if (searchQuery) {
            const titleMatch = item.title && item.title.toLowerCase().includes(searchQuery);
            const subMatch = item.subdistrict && item.subdistrict.toLowerCase().includes(searchQuery);
            const cityMatch = item.target_city && item.target_city.toLowerCase().includes(searchQuery);
            if (!titleMatch && !subMatch && !cityMatch) return false;
        }
        return true;
    });

    // Sorting
    if (sortOrder === 'price-asc') {
        filtered.sort((a, b) => a.price_monthly_idr - b.price_monthly_idr);
    } else if (sortOrder === 'price-desc') {
        filtered.sort((a, b) => b.price_monthly_idr - a.price_monthly_idr);
    } else if (sortOrder === 'deal-desc') {
        filtered.sort((a, b) => a.deal_score_z - b.deal_score_z);
    } else if (sortOrder === 'm2-asc') {
        filtered.sort((a, b) => a.price_per_m2_idr - b.price_per_m2_idr);
    } else if (sortOrder === 'size-desc') {
        filtered.sort((a, b) => b.floor_size_m2 - a.floor_size_m2);
    }

    AppState.currentFilteredListings = filtered;

    const countFilteredEl = document.getElementById('count-filtered');
    const unitWord = typeof t === 'function' ? t('units_count', 'unit') : 'unit';
    const isEn = (AppState.currentLanguage === 'en');
    if (countFilteredEl) {
        countFilteredEl.innerText = isEn ? `${filtered.length} ${unitWord} displayed` : `${filtered.length} ${unitWord} ditampilkan`;
    }
    renderDistrictsGrid();

    const subLabel = document.getElementById('tab1-subdistrict-label');
    if (subLabel) {
        const modePrefix = AppState.currentInventoryMode === 'deals' ? (isEn ? '⚡ Deals in ' : '⚡ Unit hemat di ') : '';
        const regionDefault = isEn ? 'Greater Jakarta' : 'Jabodetabek';
        subLabel.innerText = selectedSubdistrict !== 'All'
            ? `${modePrefix}${selectedSubdistrict} (${filtered.length} ${unitWord})`
            : (selectedCity !== 'All' ? `${modePrefix}${selectedCity} (${filtered.length} ${unitWord})` : `${modePrefix}${regionDefault} (${filtered.length} ${unitWord})`);
    }

    renderListingsCards(filtered);
}
window.applyFilters = applyFilters;

function cleanDisplayTitle(item) {
    if (!item || !item.title) return `Apartemen ${item?.subdistrict || 'Jabodetabek'}`;
    if (item.title.includes('•')) return item.title;

    let t = item.title;
    t = t.replace(/^(disewakan|disewa|di sewakan|sewa|for rent|for lease|rent a)\s+(apartemen|apartment|apartement|condominium|unit)?\s*/i, '');
    t = t.replace(/^\[[A-Za-z0-9]+\]\s*/, '');
    t = t.replace(/\s+(siap\s+huni|unit\s+bagus|fully?\s+furnished|murah|termurah|mewah|connect\s+mall|dekat\s+mrt|dekat\s+tol).*$/i, '');
    t = t.replace(/[,;!*]+$/, '').trim();

    const layout = item.layout_category || 'Unit';
    const isEn = (AppState.currentLanguage === 'en');
    const furnish = item.is_full_furnished ? 'Furnished' : (item.is_semi_furnished ? (isEn ? 'Semi-Furnished' : 'Semi') : (isEn ? 'Unfurnished' : 'Kosongan'));
    const size = item.floor_size_m2 ? ` (${item.floor_size_m2} m²)` : '';

    return `${t || ('Apartemen ' + item.subdistrict)} • ${layout} ${furnish}${size}`;
}

function renderListingsCards(filtered) {
    const tab1Container = document.getElementById('tab1-listings-container');
    const paginationStatus = document.getElementById('pagination-status');
    const btnLoadMore = document.getElementById('btn-load-more');
    if (!tab1Container) return;

    if (filtered.length === 0) {
        tab1Container.innerHTML = `<div style="color: var(--color-fog); padding: 36px; text-align: center; font-size: 13px; grid-column: 1 / -1;">${typeof t === 'function' ? t('no_listings_found', 'Tidak ada unit yang cocok dengan kriteria filter.') : 'Tidak ada unit yang cocok dengan kriteria filter.'}</div>`;
        if (paginationStatus) paginationStatus.innerText = typeof t === 'function' ? t('showing_units', 'Menampilkan 0 dari 0 unit').replace('{visible}', '0').replace('{total}', '0') : 'Menampilkan 0 dari 0 unit';
        if (btnLoadMore) btnLoadMore.style.display = 'none';
        return;
    }

    const visibleSlice = filtered.slice(0, AppState.visibleListingsCount);
    if (paginationStatus) {
        const statusPattern = typeof t === 'function' ? t('showing_units', 'Menampilkan {visible} dari {total} unit') : 'Menampilkan {visible} dari {total} unit';
        paginationStatus.innerText = statusPattern.replace('{visible}', visibleSlice.length).replace('{total}', filtered.length);
    }
    if (btnLoadMore) {
        btnLoadMore.style.display = (AppState.visibleListingsCount >= filtered.length) ? 'none' : 'inline-block';
    }

    const askingText = typeof t === 'function' ? t('card_asking_rent', 'Harga sewa') : 'Harga sewa';
    const fairEstText = typeof t === 'function' ? t('card_fair_est', 'Estimasi wajar') : 'Estimasi wajar';
    const savingsText = typeof t === 'function' ? t('card_savings', 'Hemat') : 'Hemat';
    const viewText = typeof t === 'function' ? t('card_view_listing', 'Lihat listing') : 'Lihat listing';
    const deepBadge = typeof t === 'function' ? t('deal_deep_badge', '🔥 Nilai tinggi') : '🔥 Nilai tinggi';
    const goodBadge = typeof t === 'function' ? t('deal_good_badge', '✨ Hemat') : '✨ Hemat';
    const perMonth = typeof t === 'function' ? t('per_month', '/ bln') : '/ bln';
    const jtWord = typeof t === 'function' ? t('unit_million', 'jt') : 'jt';
    const rbWord = typeof t === 'function' ? t('unit_thousand', 'rb') : 'rb';
    const perM2 = typeof t === 'function' ? t('per_m2', '/m²') : '/m²';

    const cardsHtml = visibleSlice.map(item => {
        // Data ini hasil scraping -> tidak terpercaya. URL divalidasi skemanya,
        // seluruh teks di-escape sebelum masuk innerHTML.
        const cleanUrl = window.safeExternalUrl(item.url, 'https://www.rumah123.com');
        // Ambang dari server; bila belum termuat, jangan menandai deal sama sekali.
        const thresholds = AppState.dealThresholds;
        const z = item.deal_score_z;
        const isDeal = !!(thresholds && z <= thresholds.good_z);
        const isDeep = !!(thresholds && z <= thresholds.deep_z);
        const displayTitle = escapeHtml(cleanDisplayTitle(item));
        const cityLabel = escapeHtml(item.target_city);
        const subdistrictLabel = escapeHtml(item.subdistrict);
        const layoutLabel = escapeHtml(item.layout_category);

        let dealPricingBlock = '';
        if (isDeal) {
            const fairEst = item.fair_market_rent_idr || (item.price_monthly_idr * (1 + (item.discount_pct || 20) / 100));
            const savings = Math.max(0, fairEst - item.price_monthly_idr);
            const discount = item.discount_pct ? Math.round(item.discount_pct) : Math.round((savings / fairEst) * 100);
            dealPricingBlock = `
                <div class="deal-pricing-block">
                    <div>
                        <div style="font-size: 10px; color: var(--color-fog);">${askingText}</div>
                        <div class="mono" style="font-size: 13px; color: var(--color-carbon-ink); font-weight: 600;">Rp ${(item.price_monthly_idr / 1e6).toFixed(1)} ${jtWord}</div>
                    </div>
                    <div>
                        <div style="font-size: 10px; color: var(--color-fog);">${fairEstText}</div>
                        <div class="mono" style="font-size: 13px; color: var(--color-fog); font-weight: 500;">Rp ${(fairEst / 1e6).toFixed(1)} ${jtWord}</div>
                    </div>
                    <div>
                        <div style="font-size: 10px; color: var(--color-carbon-ink); font-weight: 600;">${savingsText}</div>
                        <div class="mono" style="font-size: 13px; color: var(--color-carbon-ink); font-weight: 700;">-${discount}%</div>
                    </div>
                </div>
            `;
        }

        const furnishTag = item.is_full_furnished
            ? (typeof t === 'function' ? t('tag_furnished', 'Furnished') : 'Furnished')
            : (item.is_semi_furnished
                ? (typeof t === 'function' ? t('tag_semi_furnished', 'Semi') : 'Semi')
                : (typeof t === 'function' ? t('tag_unfurnished', 'Kosongan') : 'Kosongan'));

        return `
            <div class="listing-card${isDeal ? ' is-deal' : ''}">
                <div>
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                        <div class="mono" style="font-size: 10px; color: var(--color-fog);">
                            ${cityLabel} • ${subdistrictLabel}
                        </div>
                        ${isDeal ? `<span class="mono" style="font-size: 10px; ${isDeep ? 'background: var(--color-carbon-ink); color: var(--color-paper-white);' : 'background: var(--color-newsprint-gray); color: var(--color-carbon-ink); border: 1px solid var(--color-pebble);'} padding: 3px 8px; border-radius: var(--radius-pills); font-weight: 600; letter-spacing: 0.02em;">${isDeep ? deepBadge : goodBadge}</span>` : ''}
                    </div>
                    <h4 style="font-size: 14px; font-weight: 600; color: var(--color-carbon-ink); margin-bottom: 8px; line-height: 1.4;">${displayTitle}</h4>
                    <div style="font-size: 11px; color: var(--color-fog); margin-bottom: 10px; display: flex; flex-wrap: wrap; gap: 6px;">
                        <span class="mono" style="background: var(--color-newsprint-gray); border: 1px solid var(--color-pebble); padding: 2px 6px; border-radius: 4px; color: var(--color-carbon-ink);">📐 ${item.floor_size_m2} m²</span>
                        <span class="mono" style="background: var(--color-newsprint-gray); border: 1px solid var(--color-pebble); padding: 2px 6px; border-radius: 4px; color: var(--color-carbon-ink);">🛏️ ${layoutLabel}</span>
                        <span style="background: var(--color-newsprint-gray); border: 1px solid var(--color-pebble); padding: 2px 6px; border-radius: 4px; color: var(--color-carbon-ink);">🛋️ ${furnishTag}</span>
                    </div>
                    ${dealPricingBlock}
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--color-pebble); padding-top: 12px; margin-top: 8px;">
                    <div>
                        ${!isDeal ? `
                        <div style="font-size: 9px; color: var(--color-fog);">${askingText}</div>
                        <div class="mono" style="font-size: 15px; color: var(--color-carbon-ink); font-weight: 600;">
                            Rp ${(item.price_monthly_idr / 1e6).toFixed(1)} ${jtWord} <span style="font-size: 10px; color: var(--color-fog); font-weight: 400;">${perMonth}</span>
                        </div>
                        ` : `
                        <div class="mono" style="font-size: 11px; color: var(--color-fog);">
                            Rp ${Math.round(item.price_per_m2_idr / 1000)} ${rbWord}${perM2}
                        </div>
                        `}
                    </div>
                    <a href="${cleanUrl}" target="_blank" rel="noopener noreferrer" class="btn-action-dark" style="padding: 6px 12px; font-size: 12px; text-decoration: none;">
                        <span>${viewText}</span>
                        <span class="btn-bubble-icon">↗</span>
                    </a>
                </div>
            </div>
        `;
    }).join('');

    tab1Container.innerHTML = cardsHtml;
}
window.renderListingsCards = renderListingsCards;

function renderBenchmarkTable(cities) {
    const tbody = document.getElementById('benchmark-tbody');
    if (!tbody || !cities) return;
    tbody.innerHTML = '';
    const jtWord = typeof t === 'function' ? t('unit_million', 'jt') : 'jt';
    const rbWord = typeof t === 'function' ? t('unit_thousand', 'rb') : 'rb';
    const perM2 = typeof t === 'function' ? t('per_m2', '/m²') : '/m²';
    cities.forEach(c => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td style="font-weight: 600; color: var(--color-carbon-ink);">${escapeHtml(c.target_city)}</td>
            <td class="mono" style="color: var(--color-fog);">${c.sample_size}</td>
            <td class="mono">Rp ${(c.median_rent_idr / 1e6).toFixed(1)} ${jtWord}</td>
            <td class="mono" style="color: var(--color-carbon-ink); font-weight: 600;">Rp ${Math.round(c.median_price_per_m2_idr / 1000)} ${rbWord}${perM2}</td>
        `;
        tbody.appendChild(row);
    });
}
window.renderBenchmarkTable = renderBenchmarkTable;

