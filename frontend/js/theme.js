/**
 * theme.js
 * Theme Management Engine (Light & Dark Mode)
 */

function getTheme() {
    return localStorage.getItem('hi_theme') || 'light';
}

function setTheme(theme) {
    if (theme !== 'dark' && theme !== 'light') theme = 'light';

    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('hi_theme', theme);

    if (window.AppState) {
        window.AppState.currentTheme = theme;
    }

    // Update Theme Toggle Button Icon & Label
    const iconEl = document.getElementById('theme-icon');
    const toggleBtn = document.getElementById('theme-toggle-btn');
    if (iconEl) {
        iconEl.innerText = theme === 'dark' ? '☀️' : '🌙';
    }
    if (toggleBtn) {
        toggleBtn.setAttribute('title', theme === 'dark' ? 'Mode terang / Light mode' : 'Mode gelap / Dark mode');
    }

    // Refresh Chart.js colors if rendered
    if (window.AppState && window.AppState.decayData && typeof window.renderDecayChart === 'function') {
        window.renderDecayChart(window.AppState.decayData.points);
    }
}
window.setTheme = setTheme;

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || getTheme();
    const nextTheme = current === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);
}
window.toggleTheme = toggleTheme;

function initTheme() {
    const saved = getTheme();
    setTheme(saved);
}
window.initTheme = initTheme;

