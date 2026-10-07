/**
 * auth.js
 * Modal Authentication & Persona Role Management
 */

function openLoginModal() {
    const modal = document.getElementById('login-modal');
    if (modal) modal.classList.add('active');
}
window.openLoginModal = openLoginModal;

function closeLoginModal() {
    const modal = document.getElementById('login-modal');
    if (modal) modal.classList.remove('active');
}
window.closeLoginModal = closeLoginModal;

function selectPersonaOption(role) {
    AppState.selectedModalRole = role;
    const cards = document.querySelectorAll('.persona-choice-card');
    if (cards.length >= 2) {
        cards[0].classList.toggle('selected', role === 'renter');
        cards[1].classList.toggle('selected', role === 'investor');
    }
}
window.selectPersonaOption = selectPersonaOption;

function confirmLoginSelection() {
    closeLoginModal();
    if (AppState.selectedModalRole === 'investor') {
        setInvestorRole(true);
        switchTab('tab-investor');
    } else {
        setInvestorRole(false);
        switchTab('tab-map');
    }
}
window.confirmLoginSelection = confirmLoginSelection;

function setInvestorRole(isInvestor) {
    AppState.currentUserRole = isInvestor ? 'investor' : 'guest';
    localStorage.setItem('hi_user_role', AppState.currentUserRole);

    const authContainer = document.getElementById('auth-container');
    const lockedView = document.getElementById('investor-locked-view');
    const unlockedView = document.getElementById('investor-unlocked-view');
    const lockBadge = document.getElementById('investor-lock-badge');

    const isEn = (AppState.currentLanguage === 'en');
    const profileLabel = typeof t === 'function' ? t('topbar_active_profile', 'Profil aktif:') : 'Profil aktif:';
    const investorWord = typeof t === 'function' ? t('investor_pro', 'investor pro') : 'investor pro';
    const signoutWord = typeof t === 'function' ? t('topbar_signout', 'Keluar') : 'Keluar';
    const loginWord = typeof t === 'function' ? t('topbar_login_full', 'Masuk / Akses investor pro') : 'Masuk / Akses investor pro';
    const unlockedBadgeWord = typeof t === 'function' ? t('badge_unlocked', 'Terbuka') : 'Terbuka';
    const lockedBadgeWord = typeof t === 'function' ? t('badge_locked', 'Pro') : 'Pro';

    if (isInvestor) {
        if (authContainer) {
            authContainer.innerHTML = `
                <div class="user-profile-badge">
                    <span>🏢 Bu Sarah (${investorWord})</span>
                    <button class="btn-logout" onclick="logoutInvestor()">${signoutWord}</button>
                </div>
            `;
        }
        if (lockedView) lockedView.style.display = 'none';
        if (unlockedView) unlockedView.style.display = 'block';
        if (lockBadge) {
            lockBadge.innerText = unlockedBadgeWord;
            lockBadge.style.color = 'var(--color-paper-white)';
            lockBadge.style.borderColor = 'var(--color-carbon-ink)';
            lockBadge.style.backgroundColor = 'var(--color-carbon-ink)';
        }
    } else {
        if (authContainer) {
            authContainer.innerHTML = `
                <button class="btn-nav-login" onclick="openLoginModal()">
                    <span>${loginWord}</span>
                    <span class="btn-bubble-icon">↗</span>
                </button>
            `;
        }
        if (lockedView) lockedView.style.display = 'block';
        if (unlockedView) unlockedView.style.display = 'none';
        if (lockBadge) {
            lockBadge.innerText = lockedBadgeWord;
            lockBadge.style.color = 'var(--color-carbon-ink)';
            lockBadge.style.borderColor = 'var(--color-carbon-ink)';
            lockBadge.style.backgroundColor = 'var(--color-newsprint-gray)';
        }
    }
}
window.setInvestorRole = setInvestorRole;

