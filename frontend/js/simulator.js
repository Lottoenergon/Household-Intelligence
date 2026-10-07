/**
 * simulator.js
 * Tab 2: Smart Rent Valuation Simulator (Hedonic AVM)
 */

const BEDROOM_PRESETS = {
    0: { typicalSize: 28, typicalBaths: 1, minRealisticSize: 18, maxRealisticSize: 45, labelId: '20–35 m²', labelEn: '20–35 m²' },
    1: { typicalSize: 45, typicalBaths: 1, minRealisticSize: 28, maxRealisticSize: 70, labelId: '35–55 m²', labelEn: '35–55 m²' },
    2: { typicalSize: 70, typicalBaths: 1, minRealisticSize: 48, maxRealisticSize: 110, labelId: '55–90 m²', labelEn: '55–90 m²' },
    3: { typicalSize: 120, typicalBaths: 2, minRealisticSize: 85, maxRealisticSize: 180, labelId: '95–160 m²', labelEn: '95–160 m²' },
    4: { typicalSize: 200, typicalBaths: 3, minRealisticSize: 140, maxRealisticSize: 320, labelId: '170–280 m²', labelEn: '170–280 m²' }
};

function onSimBedsChange() {
    const beds = parseInt(document.getElementById('sim-beds').value);
    const preset = BEDROOM_PRESETS[beds] || BEDROOM_PRESETS[2];
    const sizeInput = document.getElementById('sim-size');
    const bathsSelect = document.getElementById('sim-baths');

    if (sizeInput) {
        sizeInput.value = preset.typicalSize;
    }
    if (bathsSelect) {
        bathsSelect.value = preset.typicalBaths;
    }
    updateSizeHint();
    runSimulation();
}
window.onSimBedsChange = onSimBedsChange;

function updateSizeHint() {
    const bedsEl = document.getElementById('sim-beds');
    if (!bedsEl) return;
    const beds = parseInt(bedsEl.value);
    const preset = BEDROOM_PRESETS[beds] || BEDROOM_PRESETS[2];
    const isEn = (AppState.currentLanguage === 'en');
    const hintEl = document.getElementById('sim-size-hint');
    const warnEl = document.getElementById('sim-size-warning');
    const currentSize = parseFloat(document.getElementById('sim-size')?.value) || preset.typicalSize;

    if (hintEl) {
        const hintText = isEn 
            ? `Standard market size: <strong>${preset.labelEn}</strong>`
            : `Standar tipikal pasar: <strong>${preset.labelId}</strong>`;
        hintEl.innerHTML = hintText;
    }

    if (warnEl) {
        if (currentSize < preset.minRealisticSize) {
            warnEl.style.display = 'block';
            warnEl.innerHTML = isEn
                ? `⚠️ <strong>Note:</strong> ${currentSize} m² is unusually compact for a ${beds}-bedroom apartment (standard market size: ${preset.labelEn}). Estimate has been calibrated to remain realistic.`
                : `⚠️ <strong>Perhatian:</strong> Ukuran ${currentSize} m² tergolong sangat kecil untuk apartemen ${beds} kamar (biasanya ${preset.labelId}). Estimasi harga telah disesuaikan agar tetap realistis.`;
        } else {
            warnEl.style.display = 'none';
        }
    }
}
window.updateSizeHint = updateSizeHint;

function updateSimSubdistricts() {
    const city = document.getElementById('sim-city').value;
    const sel = document.getElementById('sim-subdistrict');
    if (!sel) return;
    const currentVal = sel.value;
    const defaultLabel = typeof t === 'function' ? t('sim_subdistrict_default', 'Semua distrik (median kota)') : 'Semua distrik (median kota)';
    sel.innerHTML = `<option value="">${defaultLabel}</option>`;

    const matched = AppState.allDistricts.filter(d => d.target_city === city);
    matched.forEach(d => {
        const opt = document.createElement('option');
        opt.value = d.subdistrict;
        opt.innerText = `${d.subdistrict} (Median: Rp ${Math.round(d.median_price_per_m2_idr).toLocaleString('id-ID')}/m²)`;
        sel.appendChild(opt);
    });
    if (matched.some(d => d.subdistrict === currentVal)) {
        sel.value = currentVal;
    }
    onSimSubdistrictChange();
}
window.updateSimSubdistricts = updateSimSubdistricts;

function onSimCityChange() {
    updateSimSubdistricts();
}
window.onSimCityChange = onSimCityChange;

function onSimSubdistrictChange() {
    const city = document.getElementById('sim-city').value;
    const sub = document.getElementById('sim-subdistrict').value;
    const found = AppState.allDistricts.find(d => d.target_city === city && d.subdistrict === sub);
    const isEn = (AppState.currentLanguage === 'en');
    const unitWord = typeof t === 'function' ? t('units_count', 'unit') : 'unit';

    const baselineBox = document.getElementById('sim-subdistrict-baseline');
    if (found && baselineBox) {
        baselineBox.style.display = 'block';
        const titleText = isEn ? `📍 <strong>Market benchmark for ${found.subdistrict}:</strong> Median rate <strong>Rp ${Math.round(found.median_price_per_m2_idr).toLocaleString('id-ID')} / m²</strong> (${found.unit_count} ${unitWord} recorded in this area).`
                               : `📍 <strong>Data pasaran ${found.subdistrict}:</strong> Median tarif pasaran <strong>Rp ${Math.round(found.median_price_per_m2_idr).toLocaleString('id-ID')} / m²</strong> (${found.unit_count} ${unitWord} terdata di kawasan ini).`;
        baselineBox.innerHTML = titleText;
    } else if (baselineBox) {
        baselineBox.style.display = 'none';
    }
    runSimulation();
}
window.onSimSubdistrictChange = onSimSubdistrictChange;

function onFurnishSelectChange() {
    runSimulation();
}
window.onFurnishSelectChange = onFurnishSelectChange;

async function runSimulation() {
    updateSizeHint();
    const subVal = document.getElementById('sim-subdistrict') ? document.getElementById('sim-subdistrict').value : '';
    const furnishType = document.getElementById('sim-furnish-type') ? document.getElementById('sim-furnish-type').value : 'full';

    const payload = {
        city: document.getElementById('sim-city').value,
        subdistrict: subVal || null,
        floor_size_m2: parseFloat(document.getElementById('sim-size').value) || 70,
        bedrooms: parseInt(document.getElementById('sim-beds').value) || 2,
        bathrooms: parseInt(document.getElementById('sim-baths').value) || 1,
        distance_to_cbd_km: null,
        distance_to_transit_km: null,
        is_full_furnished: (furnishType === 'full'),
        is_semi_furnished: (furnishType === 'semi'),
        has_pool: document.getElementById('sim-pool') ? document.getElementById('sim-pool').checked : true,
        has_gym: document.getElementById('sim-gym') ? document.getElementById('sim-gym').checked : false,
        has_balcony: document.getElementById('sim-balcony') ? document.getElementById('sim-balcony').checked : false,
        near_transit: document.getElementById('sim-near-transit') ? document.getElementById('sim-near-transit').checked : false,
        has_parking: document.getElementById('sim-parking') ? document.getElementById('sim-parking').checked : false
    };

    const result = await API.simulateRent(payload);
    if (!result) return;

    const isEn = (AppState.currentLanguage === 'en');
    const perMonth = typeof t === 'function' ? t('per_month', '/ bln') : '/ bln';

    if (document.getElementById('sim-output-rent')) {
        document.getElementById('sim-output-rent').innerText = 'Rp ' + result.fair_market_rent_idr.toLocaleString('id-ID') + ' ' + perMonth;
    }
    if (document.getElementById('sim-output-ci')) {
        const ciLabel = isEn ? 'Fair price range' : 'Kisaran harga wajar';
        const jtWord = typeof t === 'function' ? t('unit_million', 'jt') : 'jt';
        document.getElementById('sim-output-ci').innerText = `${ciLabel}: Rp ${(result.ci_lower_idr / 1e6).toFixed(1)} ${jtWord} – Rp ${(result.ci_upper_idr / 1e6).toFixed(1)} ${jtWord} ${perMonth}`;
    }
    if (document.getElementById('sim-output-rate')) {
        const rateLabel = typeof t === 'function' ? t('sim_rate_label', 'Biaya per meter:') : 'Biaya per meter:';
        document.getElementById('sim-output-rate').innerText = `${rateLabel} Rp ${Math.round(result.implicit_rate_per_m2_idr).toLocaleString('id-ID')} / m²`;
    }

    // Update Bu Sarah Section if open
    if (result.furnishing_analysis) {
        const fa = result.furnishing_analysis;
        const jtWord = typeof t === 'function' ? t('unit_million', 'jt') : 'jt';
        if (document.getElementById('pro-roi-monthly')) document.getElementById('pro-roi-monthly').innerText = '+Rp ' + fa.monthly_extra_cashflow_idr.toLocaleString('id-ID');
        if (document.getElementById('pro-roi-annual')) document.getElementById('pro-roi-annual').innerText = '+Rp ' + (fa.annual_extra_cashflow_idr / 1e6).toFixed(1) + ' ' + jtWord;
        if (document.getElementById('pro-roi-cost')) document.getElementById('pro-roi-cost').innerText = 'Rp ' + fa.estimated_fitout_cost_idr.toLocaleString('id-ID');
        if (document.getElementById('pro-roi-payback')) {
            const noPrem = isEn ? 'No model premium detected' : 'Tidak ada premi dari model';
            const bepText = isEn ? `${fa.payback_period_years} years (${fa.payback_period_months} months)` : `${fa.payback_period_years} tahun (${fa.payback_period_months} bulan)`;
            document.getElementById('pro-roi-payback').innerText = fa.payback_period_months === null ? noPrem : bepText;
        }
    }
}
window.runSimulation = runSimulation;

