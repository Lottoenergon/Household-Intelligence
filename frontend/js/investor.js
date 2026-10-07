/**
 * investor.js
 * Tab 3: Pro Investor Portal & Yield Analysis (Bu Sarah)
 */

function renderDecayChart(points) {
    const chartCanvas = document.getElementById('decayChart');
    if (!chartCanvas || typeof Chart === 'undefined') return;
    const ctx = chartCanvas.getContext('2d');
    const scatterData = (points || []).map(p => ({
        x: p.distance_to_cbd_km,
        y: p.price_per_m2_idr
    }));

    if (AppState.decayChartInstance) {
        AppState.decayChartInstance.destroy();
    }

    const isDark = (document.documentElement.getAttribute('data-theme') === 'dark');
    const pointColor = isDark ? '#f4f4f6' : '#1c1c1e';
    const gridColor = isDark ? '#26262b' : '#eaeaea';
    const textColor = isDark ? '#f4f4f6' : '#1c1c1e';
    const subTextColor = isDark ? '#a1a1aa' : '#6e6e73';

    AppState.decayChartInstance = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: typeof t === 'function' ? t('decay_chart_label', 'Tarif sewa (Rp/m² vs jarak CBD)') : 'Tarif sewa (Rp/m² vs jarak CBD)',
                data: scatterData,
                backgroundColor: pointColor,
                borderColor: pointColor,
                pointRadius: 2.5,
                pointHoverRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: { display: true, text: typeof t === 'function' ? t('decay_x_title', 'Jarak ke Sudirman CBD (km)') : 'Jarak ke Sudirman CBD (km)', color: textColor, font: { weight: '500' } },
                    grid: { color: gridColor },
                    ticks: { color: subTextColor }
                },
                y: {
                    title: { display: true, text: typeof t === 'function' ? t('decay_y_title', 'Tarif per m² (Rp)') : 'Tarif per m² (Rp)', color: textColor, font: { weight: '500' } },
                    grid: { color: gridColor },
                    ticks: {
                        color: subTextColor,
                        callback: val => 'Rp ' + (val / 1000) + ' rb'
                    }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}
window.renderDecayChart = renderDecayChart;

function renderZonesTable(zones) {
    const tbody = document.getElementById('zones-tbody');
    if (!tbody || !zones) return;
    tbody.innerHTML = '';
    const unitText = typeof t === 'function' ? t('units_count', 'unit') : 'unit';
    zones.forEach(z => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td style="font-weight: 600; color: var(--color-carbon-ink);">${z.urban_zone}</td>
            <td class="mono" style="color: var(--color-fog);">${z.sample_units} ${unitText}</td>
            <td class="mono" style="color: var(--color-carbon-ink); font-weight: 600;">Rp ${Math.round(z.median_price_per_m2).toLocaleString('id-ID')}</td>
            <td class="mono">Rp ${Math.round(z.mean_price_per_m2).toLocaleString('id-ID')}</td>
        `;
        tbody.appendChild(row);
    });
}
window.renderZonesTable = renderZonesTable;

function demoLoginInvestor() {
    setInvestorRole(true);
    switchTab('tab-investor');
}
window.demoLoginInvestor = demoLoginInvestor;

function logoutInvestor() {
    setInvestorRole(false);
    switchTab('tab-map');
}
window.logoutInvestor = logoutInvestor;

