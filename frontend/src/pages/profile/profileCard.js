import { state, login, setUser } from '../../services/state.js';
import { uploadAvatar, updateProfile } from '../../services/api_v2.js';
import { escapeHtml } from '../../utils/escapeHtml.js';
import { showToast } from '../../utils/toast.js';

function avatarMarkup(profile) {
    if (profile.avatar) return `<img class="avatar" src="${escapeHtml(profile.avatar)}" alt="" />`;
    const initial = (profile.username || '?').charAt(0).toUpperCase();
    return `<div class="avatar avatar-fallback">${escapeHtml(initial)}</div>`;
}

/** Avatar + collapsible "edit account" form. */
export function renderProfileCard(profile, showEditForm) {
    const google = !profile.has_password;
    return `
    <section class="panel">
      <div class="profile-head">
        ${avatarMarkup(profile)}
        <div>
          <p class="profile-name">${escapeHtml(profile.username)}</p>
          <p class="muted">${escapeHtml(profile.email)}</p>
          ${profile.is_admin ? '<span class="tag tag-admin">Store admin</span>' : ''}
          ${google ? '<span class="tag tag-google">Google sign-in</span>' : ''}
        </div>
      </div>
      <label class="btn btn-outline btn-small file-btn">
        Change photo
        <input type="file" id="avatarInput" accept="image/png, image/jpeg, image/webp, image/gif" hidden />
      </label>
      <small class="muted block">JPEG, PNG, WebP or GIF, up to 2 MB.</small>
    </section>

    <section class="panel">
      <button class="collapse-head" id="toggleEditForm" aria-expanded="${showEditForm}">
        <h2>Edit account</h2><span aria-hidden="true">${showEditForm ? '−' : '+'}</span>
      </button>
      ${showEditForm ? `
      <form id="editForm" class="stack" novalidate>
        <label class="field"><span>Username</span>
          <input class="input" id="editUsername" value="${escapeHtml(profile.username)}" autocomplete="username" /></label>
        <label class="field"><span>Email</span>
          <input class="input" type="email" id="editEmail" value="${escapeHtml(profile.email)}" ${google ? 'disabled' : ''} autocomplete="email" />
          ${google ? '<small>Your email comes from Google and can’t be changed here.</small>' : ''}</label>
        <label class="field"><span>${google ? 'Set a password (optional)' : 'New password'}</span>
          <input class="input" type="password" id="editPassword" placeholder="Leave blank to keep it" autocomplete="new-password" /></label>
        ${google ? '' : `
        <label class="field"><span>Current password</span>
          <input class="input" type="password" id="editCurrentPassword" autocomplete="current-password" required />
          <small>Needed to save any change.</small></label>`}
        <button id="saveProfileBtn" class="btn btn-primary btn-block" type="submit">Save changes</button>
      </form>` : ''}
    </section>`;
}

/** Avatar upload + save. `onSaved` runs after a successful save (the caller collapses the form). */
export function setupProfileCardEvents(profile, rerender, onSaved) {
    document.getElementById('avatarInput')?.addEventListener('change', async (e) => {
        const file = e.target.files?.[0];
        if (!file) return;
        try {
            const result = await uploadAvatar(file);
            setUser({ ...state.user, avatar: result.avatar });
            showToast('Photo updated');
            rerender();
        } catch (err) {
            showToast(err.message, 'error');
        }
    });

    document.getElementById('editForm')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const google = !profile.has_password;
        const newUsername = document.getElementById('editUsername').value.trim();
        const newEmail = google ? '' : document.getElementById('editEmail').value.trim();
        const newPassword = document.getElementById('editPassword').value;
        const currentPassword = google ? '' : document.getElementById('editCurrentPassword').value;

        if (!google && !currentPassword) {
            showToast('Enter your current password to save changes.', 'info');
            return;
        }
        const btn = document.getElementById('saveProfileBtn');
        btn.textContent = 'Saving…';
        btn.disabled = true;
        try {
            const result = await updateProfile({
                currentPassword,
                newUsername: newUsername !== profile.username ? newUsername : null,
                newEmail: newEmail && newEmail !== profile.email ? newEmail : null,
                newPassword: newPassword || null,
            });
            login(result); // carries a fresh token if the password/email changed
            showToast('Account updated');
            onSaved();
        } catch (err) {
            showToast(err.message, 'error');
            btn.textContent = 'Save changes';
            btn.disabled = false;
        }
    });
}
