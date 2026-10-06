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
    sel.innerHTML = '<option value="All">All Districts in this City</option>';

    const matched = AppState.allDistricts.filter(d => city === 'All' || d.target_city === city);
    matched.forEach(d => {
        const opt = document.createElement('option');
        opt.value = d.subdistrict;
        opt.innerText = `${d.subdistrict} (${d.unit_count} units)`;
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

    if (badge) {
        badge.innerText = `${matched.length} Districts ${AppState.currentInventoryMode === 'deals' ? 'with Deals' : 'Monitored'}`;
    }

    if (matched.length === 0) {
        container.innerHTML = '<div style="color: var(--color-fog); padding: 16px; font-size: 12px;">No districts match the selected criteria.</div>';
        return;
    }

    const cardsHtml = matched.map(d => {
        const isActive = (selectedSub !== 'All' && d.subdistrict === selectedSub);
        const safeSub = d.subdistrict.replace(/'/g, "\\'");
        const safeCity = d.target_city.replace(/'/g, "\\'");
        return `
            <div class="district-card ${isActive ? 'active' : ''}" onclick="selectDistrict('${safeSub}', '${safeCity}')">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px;">
                    <div>
                        <div class="mono" style="font-size: 10px; color: var(--color-fog); text-transform: uppercase;">${d.target_city}</div>
                        <div style="font-size: 13px; font-weight: 600; color: var(--color-carbon-ink);">${d.subdistrict}</div>
                    </div>
                    <span class="mono" style="font-size: 10px; background: var(--color-newsprint-gray); border: 1px solid var(--color-pebble); padding: 1px 6px; border-radius: 4px; color: var(--color-carbon-ink); font-weight: 500;">${d.unit_count}</span>
                </div>
                <div style="border-top: 1px solid var(--color-pebble); padding-top: 6px; margin-top: 6px; display: flex; justify-content: space-between; align-items: baseline;">
                    <div class="mono" style="font-size: 12px; color: var(--color-carbon-ink); font-weight: 600;">
                        IDR ${(d.median_rent_idr / 1e6).toFixed(1)}M <span style="font-size: 10px; color: var(--color-fog); font-weight: 400;">/ mo</span>
                    </div>
                    <div class="mono" style="font-size: 10px; color: var(--color-fog);">
                        IDR ${Math.round(d.median_price_per_m2_idr / 1000)}k/m²
                    </div>
                </div>
                ${d.deals_count > 0 ? `<div style="font-size: 10px; color: var(--color-carbon-ink); margin-top: 4px; font-weight: 600;">⚡ ${d.deals_count} Deals Available</div>` : ''}
            </div>
        `;
    }).join('');

    container.innerHTML = cardsHtml;
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
        if (selectedLayout !== 'All' && item.layout_category !== selectedLayout) return false;
        if (maxBudget < 100000000 && item.price_monthly_idr > maxBudget) return false;
        if (furnishedOnly && !item.is_full_furnished) return false;

        if (AppState.currentInventoryMode === 'deals') {
            if (item.deal_score_z > -0.75) return false;
            if (AppState.currentDealTier === 'deep' && !(item.deal_tier === 'Deep Value' || item.deal_score_z <= -1.2)) return false;
            if (AppState.currentDealTier === 'good' && !(item.deal_tier === 'Good Deal' || (item.deal_score_z > -1.2 && item.deal_score_z <= -0.75))) return false;
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
    if (countFilteredEl) {
        countFilteredEl.innerText = `${filtered.length} Units Displayed`;
    }
    renderDistrictsGrid();

    const subLabel = document.getElementById('tab1-subdistrict-label');
    if (subLabel) {
        const modePrefix = AppState.currentInventoryMode === 'deals' ? '⚡ Deals in ' : '';
        subLabel.innerText = selectedSubdistrict !== 'All'
            ? `${modePrefix}${selectedSubdistrict} (${filtered.length} units)`
            : (selectedCity !== 'All' ? `${modePrefix}${selectedCity} (${filtered.length} units)` : `${modePrefix}Greater Jakarta (${filtered.length} units)`);
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
    const furnish = item.is_full_furnished ? 'Furnished' : (item.is_semi_furnished ? 'Semi' : 'Unfurnished');
    const size = item.floor_size_m2 ? ` (${item.floor_size_m2} m²)` : '';

    return `${t || ('Apartemen ' + item.subdistrict)} • ${layout} ${furnish}${size}`;
}

function renderListingsCards(filtered) {
    const tab1Container = document.getElementById('tab1-listings-container');
    const paginationStatus = document.getElementById('pagination-status');
    const btnLoadMore = document.getElementById('btn-load-more');
    if (!tab1Container) return;

    if (filtered.length === 0) {
        tab1Container.innerHTML = '<div style="color: var(--color-fog); padding: 36px; text-align: center; font-size: 13px; grid-column: 1 / -1;">No listings match the selected filter criteria.</div>';
        if (paginationStatus) paginationStatus.innerText = 'Showing 0 of 0 listings';
        if (btnLoadMore) btnLoadMore.style.display = 'none';
        return;
    }

    const visibleSlice = filtered.slice(0, AppState.visibleListingsCount);
    if (paginationStatus) {
        paginationStatus.innerText = `Showing ${visibleSlice.length} of ${filtered.length} listings`;
    }
    if (btnLoadMore) {
        btnLoadMore.style.display = (AppState.visibleListingsCount >= filtered.length) ? 'none' : 'inline-block';
    }

    const cardsHtml = visibleSlice.map(item => {
        const cleanUrl = item.url.startsWith('http') ? item.url : `https://www.rumah123.com${item.url}`;
        const isDeal = (item.deal_score_z <= -0.75);
        const isDeep = (item.deal_score_z <= -1.2 || item.deal_tier === 'Deep Value');
        const displayTitle = cleanDisplayTitle(item);

        let dealPricingBlock = '';
        if (isDeal) {
            const fairEst = item.fair_market_rent_idr || (item.price_monthly_idr * (1 + (item.discount_pct || 20) / 100));
            const savings = Math.max(0, fairEst - item.price_monthly_idr);
            const discount = item.discount_pct ? Math.round(item.discount_pct) : Math.round((savings / fairEst) * 100);
            dealPricingBlock = `
                <div class="deal-pricing-block">
                    <div>
                        <div style="font-size: 10px; color: var(--color-fog); text-transform: uppercase;">Asking Rent</div>
                        <div class="mono" style="font-size: 13px; color: var(--color-carbon-ink); font-weight: 600;">IDR ${(item.price_monthly_idr / 1e6).toFixed(1)}M</div>
                    </div>
                    <div>
                        <div style="font-size: 10px; color: var(--color-fog); text-transform: uppercase;">Fair Est.</div>
                        <div class="mono" style="font-size: 13px; color: var(--color-fog); font-weight: 500;">IDR ${(fairEst / 1e6).toFixed(1)}M</div>
                    </div>
                    <div>
                        <div style="font-size: 10px; color: var(--color-carbon-ink); text-transform: uppercase; font-weight: 600;">Savings</div>
                        <div class="mono" style="font-size: 13px; color: var(--color-carbon-ink); font-weight: 700;">-${discount}%</div>
                    </div>
                </div>
            `;
        }

        return `
            <div class="listing-card${isDeal ? ' is-deal' : ''}">
                <div>
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                        <div class="mono" style="font-size: 10px; color: var(--color-fog); text-transform: uppercase;">
                            ${item.target_city} • ${item.subdistrict}
                        </div>
                        ${isDeal ? `<span class="mono" style="font-size: 10px; ${isDeep ? 'background: var(--color-carbon-ink); color: #ffffff;' : 'background: var(--color-newsprint-gray); color: var(--color-carbon-ink); border: 1px solid var(--color-pebble);'} padding: 3px 8px; border-radius: var(--radius-pills); font-weight: 600; letter-spacing: 0.02em;">${isDeep ? '🔥 DEEP VALUE' : '✨ GOOD DEAL'}</span>` : ''}
                    </div>
                    <h4 style="font-size: 14px; font-weight: 600; color: var(--color-carbon-ink); margin-bottom: 8px; line-height: 1.4;">${displayTitle}</h4>
                    <div style="font-size: 11px; color: var(--color-fog); margin-bottom: 10px; display: flex; flex-wrap: wrap; gap: 6px;">
                        <span class="mono" style="background: var(--color-newsprint-gray); border: 1px solid var(--color-pebble); padding: 2px 6px; border-radius: 4px; color: var(--color-carbon-ink);">📐 ${item.floor_size_m2} m²</span>
                        <span class="mono" style="background: var(--color-newsprint-gray); border: 1px solid var(--color-pebble); padding: 2px 6px; border-radius: 4px; color: var(--color-carbon-ink);">🛏️ ${item.layout_category}</span>
                        <span style="background: var(--color-newsprint-gray); border: 1px solid var(--color-pebble); padding: 2px 6px; border-radius: 4px; color: var(--color-carbon-ink);">🛋️ ${item.is_full_furnished ? 'Furnished' : (item.is_semi_furnished ? 'Semi' : 'Unfurnished')}</span>
                    </div>
                    ${dealPricingBlock}
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--color-pebble); padding-top: 12px; margin-top: 8px;">
                    <div>
                        ${!isDeal ? `
                        <div style="font-size: 9px; color: var(--color-fog); text-transform: uppercase;">Asking Rent</div>
                        <div class="mono" style="font-size: 15px; color: var(--color-carbon-ink); font-weight: 600;">
                            IDR ${(item.price_monthly_idr / 1e6).toFixed(1)}M <span style="font-size: 10px; color: var(--color-fog); font-weight: 400;">/ mo</span>
                        </div>
                        ` : `
                        <div class="mono" style="font-size: 11px; color: var(--color-fog);">
                            IDR ${Math.round(item.price_per_m2_idr / 1000)}k/m²
                        </div>
                        `}
                    </div>
                    <a href="${cleanUrl}" target="_blank" class="btn-action-dark" style="padding: 6px 12px; font-size: 12px; text-decoration: none;">
                        <span>View Listing</span>
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
    cities.forEach(c => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td style="font-weight: 600; color: var(--color-carbon-ink);">${c.target_city}</td>
            <td class="mono" style="color: var(--color-fog);">${c.sample_size}</td>
            <td class="mono">IDR ${(c.median_rent_idr / 1e6).toFixed(1)}M</td>
            <td class="mono" style="color: var(--color-carbon-ink); font-weight: 600;">IDR ${Math.round(c.median_price_per_m2_idr / 1000)}k</td>
        `;
        tbody.appendChild(row);
    });
}
window.renderBenchmarkTable = renderBenchmarkTable;

