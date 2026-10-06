/**
 * simulator.js
 * Tab 2: Smart Rent Valuation Simulator (Hedonic AVM)
 */

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
        opt.innerText = `${d.subdistrict} (Median: Rp ${Math.round(d.median_price_per_m2_idr).toLocaleString()}/m²)`;
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
        const titleText = isEn ? `📍 <strong>Market benchmark for ${found.subdistrict}:</strong> Median rate <strong>Rp ${Math.round(found.median_price_per_m2_idr).toLocaleString()} / m²</strong> (${found.unit_count} ${unitWord} recorded in this area).`
                               : `📍 <strong>Data pasaran ${found.subdistrict}:</strong> Median tarif pasaran <strong>Rp ${Math.round(found.median_price_per_m2_idr).toLocaleString()} / m²</strong> (${found.unit_count} ${unitWord} terdata di kawasan ini).`;
        baselineBox.innerHTML = titleText;
    } else if (baselineBox) {
        baselineBox.style.display = 'none';
    }
    runSimulation();
}
window.onSimSubdistrictChange = onSimSubdistrictChange;

function onFurnishSelectChange() {
    const type = document.getElementById('sim-furnish-type').value;
    const ffBox = document.getElementById('sim-ff');
    if (ffBox) {
        ffBox.checked = (type === 'full');
    }
    runSimulation();
}
window.onFurnishSelectChange = onFurnishSelectChange;

async function runSimulation() {
    const subVal = document.getElementById('sim-subdistrict') ? document.getElementById('sim-subdistrict').value : '';
    const cbdInput = document.getElementById('sim-cbd');
    const transitInput = document.getElementById('sim-transit');

    const payload = {
        city: document.getElementById('sim-city').value,
        subdistrict: subVal || null,
        floor_size_m2: parseFloat(document.getElementById('sim-size').value) || 45,
        bedrooms: parseInt(document.getElementById('sim-beds').value) || 2,
        bathrooms: parseInt(document.getElementById('sim-baths').value) || 1,
        distance_to_cbd_km: (cbdInput && cbdInput.value) ? parseFloat(cbdInput.value) : null,
        distance_to_transit_km: (transitInput && transitInput.value) ? parseFloat(transitInput.value) : null,
        is_full_furnished: document.getElementById('sim-ff').checked,
        has_ac: document.getElementById('sim-ac').checked,
        has_pool: document.getElementById('sim-pool').checked,
        has_gym: document.getElementById('sim-gym').checked,
        has_balcony: document.getElementById('sim-balcony').checked,
        has_kitchen: document.getElementById('sim-kitchen').checked
    };

    const result = await API.simulateRent(payload);
    if (!result) return;

    const isEn = (AppState.currentLanguage === 'en');
    const perMonth = typeof t === 'function' ? t('per_month', '/ bln') : '/ bln';

    if (document.getElementById('sim-output-rent')) {
        document.getElementById('sim-output-rent').innerText = 'Rp ' + result.fair_market_rent_idr.toLocaleString() + ' ' + perMonth;
    }
    if (document.getElementById('sim-output-ci')) {
        const ciLabel = isEn ? `Market tolerance range ${result.interval_level_pct}%` : `Rentang toleransi pasar ${result.interval_level_pct}%`;
        const jtWord = isEn ? 'M' : 'jt';
        document.getElementById('sim-output-ci').innerText = `${ciLabel}: Rp ${(result.ci_lower_idr / 1e6).toFixed(1)} ${jtWord} – Rp ${(result.ci_upper_idr / 1e6).toFixed(1)} ${jtWord} ${perMonth}`;
    }
    if (document.getElementById('sim-output-rate')) {
        const rateLabel = typeof t === 'function' ? t('sim_rate_label', 'Tarif efektif ruang:') : 'Tarif efektif ruang:';
        document.getElementById('sim-output-rate').innerText = `${rateLabel} Rp ${result.implicit_rate_per_m2_idr.toLocaleString()} / m²`;
    }

    // Update Bu Sarah Section if open
    if (result.furnishing_analysis) {
        const fa = result.furnishing_analysis;
        const jtWord = isEn ? 'M' : 'jt';
        if (document.getElementById('pro-roi-monthly')) document.getElementById('pro-roi-monthly').innerText = '+Rp ' + fa.monthly_extra_cashflow_idr.toLocaleString();
        if (document.getElementById('pro-roi-annual')) document.getElementById('pro-roi-annual').innerText = '+Rp ' + (fa.annual_extra_cashflow_idr / 1e6).toFixed(1) + ' ' + jtWord;
        if (document.getElementById('pro-roi-cost')) document.getElementById('pro-roi-cost').innerText = 'Rp ' + fa.estimated_fitout_cost_idr.toLocaleString();
        if (document.getElementById('pro-roi-payback')) {
            const noPrem = isEn ? 'No model premium detected' : 'Tidak ada premi dari model';
            const bepText = isEn ? `${fa.payback_period_years} years (${fa.payback_period_months} months)` : `${fa.payback_period_years} tahun (${fa.payback_period_months} bulan)`;
            document.getElementById('pro-roi-payback').innerText = fa.payback_period_months === null ? noPrem : bepText;
        }
    }
}
window.runSimulation = runSimulation;

