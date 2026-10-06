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

    if (isInvestor) {
        if (authContainer) {
            authContainer.innerHTML = `
                <div class="user-profile-badge">
                    <span>🏢 Bu Sarah (Investor)</span>
                    <button class="btn-logout" onclick="logoutInvestor()">Sign Out</button>
                </div>
            `;
        }
        if (lockedView) lockedView.style.display = 'none';
        if (unlockedView) unlockedView.style.display = 'block';
        if (lockBadge) {
            lockBadge.innerText = 'TERBUKA';
            lockBadge.style.color = '#ffffff';
            lockBadge.style.borderColor = 'var(--color-carbon-ink)';
            lockBadge.style.backgroundColor = 'var(--color-carbon-ink)';
        }
    } else {
        if (authContainer) {
            authContainer.innerHTML = `
                <button class="btn-nav-login" onclick="openLoginModal()">
                    <span>Sign In / Pro Investor Access</span>
                    <span class="btn-bubble-icon">↗</span>
                </button>
            `;
        }
        if (lockedView) lockedView.style.display = 'block';
        if (unlockedView) unlockedView.style.display = 'none';
        if (lockBadge) {
            lockBadge.innerText = 'PRO';
            lockBadge.style.color = 'var(--color-carbon-ink)';
            lockBadge.style.borderColor = 'var(--color-carbon-ink)';
            lockBadge.style.backgroundColor = 'var(--color-newsprint-gray)';
        }
    }
}
window.setInvestorRole = setInvestorRole;

