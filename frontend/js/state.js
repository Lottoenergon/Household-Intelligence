/**
 * state.js
 * Centralized Application State Management for Household Intelligence
 */

const AppState = {
    allListings: [],
    allDistricts: [],
    allBenchmarks: {},
    decayData: {},
    currentUserRole: 'guest', // 'guest', 'renter', 'investor'
    selectedModalRole: 'investor',
    currentInventoryMode: 'all', // 'all' or 'deals'
    currentDealTier: 'all', // 'all', 'deep', 'good'
    decayChartInstance: null,
    visibleListingsCount: 60,
    currentFilteredListings: [],
    searchDebounceTimer: null
};

// Window-level references for cross-module compatibility
window.AppState = AppState;

