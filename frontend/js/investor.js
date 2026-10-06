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

    AppState.decayChartInstance = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Tarif Sewa (Rp/m² vs Jarak CBD)',
                data: scatterData,
                backgroundColor: '#222222',
                borderColor: '#222222',
                pointRadius: 2.5,
                pointHoverRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: { display: true, text: 'Jarak ke Sudirman CBD (km)', color: '#222222', font: { weight: '500' } },
                    grid: { color: '#ebebeb' },
                    ticks: { color: '#6a6a6a' }
                },
                y: {
                    title: { display: true, text: 'Tarif per m² (Rp)', color: '#222222', font: { weight: '500' } },
                    grid: { color: '#ebebeb' },
                    ticks: {
                        color: '#6a6a6a',
                        callback: val => 'Rp ' + (val / 1000) + 'k'
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
    zones.forEach(z => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td style="font-weight: 600; color: var(--color-carbon-ink);">${z.urban_zone}</td>
            <td class="mono" style="color: var(--color-fog);">${z.sample_units} Units</td>
            <td class="mono" style="color: var(--color-carbon-ink); font-weight: 600;">Rp ${Math.round(z.median_price_per_m2).toLocaleString()}</td>
            <td class="mono">Rp ${Math.round(z.mean_price_per_m2).toLocaleString()}</td>
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

