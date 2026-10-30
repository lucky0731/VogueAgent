import { logout } from '../../services/state.js';
import { deleteAccount } from '../../services/api_v2.js';
import { setCartCount } from '../../services/cartCount.js';
import { escapeHtml } from '../../utils/escapeHtml.js';
import { showToast } from '../../utils/toast.js';

/** Delete-account card. Password accounts confirm with the password; Google ones by typing their email. */
export function renderDangerZone(profile, showConfirm) {
    const google = !profile.has_password;
    return `
    <section class="panel panel-danger">
      <h2>Delete account</h2>
      ${showConfirm ? `
        <p class="muted">This permanently deletes your account, bag and order history.</p>
        <label class="field"><span>${google ? `Type ${escapeHtml(profile.email)} to confirm` : 'Your password'}</span>
          <input class="input" ${google ? 'type="email"' : 'type="password" autocomplete="current-password"'} id="deleteConfirm" /></label>
        <div class="row">
          <button id="confirmDeleteBtn" class="btn btn-danger">Delete permanently</button>
          <button id="cancelDeleteBtn" class="btn btn-ghost">Cancel</button>
        </div>
      ` : `
        <p class="muted">Remove your account and everything saved with it.</p>
        <button id="deleteAccountBtn" class="btn btn-outline btn-danger-outline">Delete account</button>
      `}
    </section>`;
}

export function setupDangerZoneEvents(profile, onDeleted) {
    document.getElementById('confirmDeleteBtn')?.addEventListener('click', async () => {
        const google = !profile.has_password;
        const value = document.getElementById('deleteConfirm').value;
        if (!value) {
            showToast(google ? 'Type your email to confirm.' : 'Enter your password.', 'info');
            return;
        }
        const btn = document.getElementById('confirmDeleteBtn');
        btn.textContent = 'Deleting…';
        btn.disabled = true;
        try {
            await deleteAccount(google ? { confirmEmail: value } : { password: value });
            logout();
            setCartCount(0);
            onDeleted();
            showToast('Your account has been deleted.', 'info');
            window.location.hash = '#/';
        } catch (err) {
            showToast(err.message, 'error');
            btn.textContent = 'Delete permanently';
            btn.disabled = false;
        }
    });
}
