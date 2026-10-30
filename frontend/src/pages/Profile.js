import { state, logout, setUser } from '../services/state.js';
import { getProfile, getOrderHistory } from '../services/api_v2.js';
import { refreshCartCount } from '../services/cartCount.js';
import { renderAuthForms, setupAuthFormsEvents } from './profile/authForms.js';
import { renderProfileCard, setupProfileCardEvents } from './profile/profileCard.js';
import { renderOrderHistory } from './profile/orderHistory.js';
import { renderDangerZone, setupDangerZoneEvents } from './profile/dangerZone.js';
import { showToast } from '../utils/toast.js';
import { escapeHtml } from '../utils/escapeHtml.js';

/**
 * Logged out: login / register forms. Logged in: profile, edit form, order
 * history and account deletion. Panel open/closed state lives in state.ui.
 */
export async function renderProfile() {
    const app = document.getElementById('app');
    if (!state.isLoggedIn) {
        app.innerHTML = renderAuthForms();
        setupAuthFormsEvents(renderProfile);
        return;
    }

    let profile = state.user;
    let orders = [];
    try {
        [profile, orders] = await Promise.all([getProfile(), getOrderHistory()]);
        setUser(profile);
    } catch (err) {
        if (!state.isLoggedIn) return renderProfile(); // session expired
        showToast(err.message, 'error');
    }

    app.innerHTML = `
    <div class="container page account">
      <h1 class="page-title">Hello, ${escapeHtml(profile.username || 'there')}</h1>
      <div class="account-grid">
        <div class="account-side">
          ${renderProfileCard(profile, state.ui.profileEditOpen)}
          ${renderDangerZone(profile, state.ui.profileDeleteOpen)}
          <button id="logoutBtn" class="btn btn-outline btn-block">Log out</button>
        </div>
        <div class="account-main">
          ${renderOrderHistory(orders)}
        </div>
      </div>
    </div>`;

    setupProfileEvents(profile);
}

function setupProfileEvents(profile) {
    document.getElementById('toggleEditForm')?.addEventListener('click', () => {
        state.ui.profileEditOpen = !state.ui.profileEditOpen;
        renderProfile();
    });
    setupProfileCardEvents(profile, renderProfile, () => {
        state.ui.profileEditOpen = false;
        renderProfile();
    });

    document.getElementById('deleteAccountBtn')?.addEventListener('click', () => {
        state.ui.profileDeleteOpen = true;
        renderProfile();
    });
    document.getElementById('cancelDeleteBtn')?.addEventListener('click', () => {
        state.ui.profileDeleteOpen = false;
        renderProfile();
    });
    setupDangerZoneEvents(profile, () => {
        state.ui.profileDeleteOpen = false;
    });

    document.getElementById('logoutBtn')?.addEventListener('click', async () => {
        logout();
        await refreshCartCount();
        showToast('You are logged out.', 'info');
        renderProfile();
    });
}
