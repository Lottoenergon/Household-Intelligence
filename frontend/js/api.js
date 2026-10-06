/**
 * api.js
 * Asynchronous Data Access Layer for Backend Endpoints
 */

const API = {
    async fetchTelemetry() {
        try {
            const res = await fetch('/api/telemetry');
            if (!res.ok) throw new Error(`HTTP error ${res.status}`);
            return await res.json();
        } catch (err) {
            console.error('Failed to fetch telemetry:', err);
            return null;
        }
    },

    async fetchBenchmarks() {
        try {
            const res = await fetch('/api/benchmarks');
            if (!res.ok) throw new Error(`HTTP error ${res.status}`);
            return await res.json();
        } catch (err) {
            console.error('Failed to fetch benchmarks:', err);
            return null;
        }
    },

    async fetchDistricts() {
        try {
            const res = await fetch('/api/districts');
            if (!res.ok) throw new Error(`HTTP error ${res.status}`);
            return await res.json();
        } catch (err) {
            console.error('Failed to fetch districts:', err);
            return null;
        }
    },

    async fetchListings(limit = 800) {
        try {
            const res = await fetch(`/api/listings?limit=${limit}`);
            if (!res.ok) throw new Error(`HTTP error ${res.status}`);
            return await res.json();
        } catch (err) {
            console.error('Failed to fetch listings:', err);
            return null;
        }
    },

    async fetchDistanceDecay() {
        try {
            const res = await fetch('/api/distance-decay');
            if (!res.ok) throw new Error(`HTTP error ${res.status}`);
            return await res.json();
        } catch (err) {
            console.error('Failed to fetch distance decay:', err);
            return null;
        }
    },

    async simulateRent(payload) {
        try {
            const res = await fetch('/api/simulate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (!res.ok) throw new Error(`HTTP error ${res.status}`);
            return await res.json();
        } catch (err) {
            console.error('Failed to run simulation:', err);
            return null;
        }
    }
};

window.API = API;

