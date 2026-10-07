/**
 * api.js
 * Asynchronous Data Access Layer for Backend Endpoints
 *
 * Semua request lewat request() supaya kegagalan TIDAK pernah senyap:
 * sebelumnya setiap method menelan error lalu `return null`, sehingga UI
 * diam-diam menampilkan angka fallback yang terlihat seperti data asli.
 * Sekarang setiap kegagalan dilaporkan lewat window.reportApiFailure().
 */

const API = (function () {
    'use strict';

    async function request(url, options) {
        try {
            const res = await fetch(url, options);
            if (!res.ok) {
                // FastAPI mengirim {"detail": "..."} — pesan itu yang paling berguna.
                let detail = '';
                try {
                    const body = await res.json();
                    if (body && body.detail) detail = String(body.detail);
                } catch (parseErr) {
                    detail = '';
                }
                throw new Error(detail || `HTTP ${res.status}`);
            }
            if (typeof window.clearApiFailure === 'function') {
                window.clearApiFailure(url);
            }
            return await res.json();
        } catch (err) {
            console.error(`[API] request gagal: ${url}`, err);
            if (typeof window.reportApiFailure === 'function') {
                window.reportApiFailure(url, err);
            }
            return null;
        }
    }

    return {
        fetchTelemetry() {
            return request('/api/telemetry');
        },
        fetchBenchmarks() {
            return request('/api/benchmarks');
        },
        fetchDistricts() {
            return request('/api/districts');
        },
        fetchListings(limit) {
            return request(`/api/listings?limit=${limit === undefined ? 800 : limit}`);
        },
        fetchDistanceDecay() {
            return request('/api/distance-decay');
        },
        simulateRent(payload) {
            return request('/api/simulate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        }
    };
})();

window.API = API;

