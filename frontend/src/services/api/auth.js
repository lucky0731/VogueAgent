import { request } from './http.js';

/** The logged-in user's profile (includes is_admin). */
export function getMe() {
    return request('/auth/me');
}

export function registerUser(username, email, password) {
    return request('/auth/register', { method: 'POST', write: true, body: { username, email, password } });
}

export function loginUser(identifier, password) {
    return request('/auth/login', { method: 'POST', write: true, body: { identifier, password } });
}

/** Google OAuth client id (public). '' when not configured. */
export async function getGoogleClientId() {
    try {
        const data = await request('/auth/google-client-id');
        return data.client_id || '';
    } catch {
        return '';
    }
}

export function googleLogin(credential) {
    return request('/auth/google', { method: 'POST', write: true, body: { credential } });
}

export function getProfile() {
    return request('/auth/profile');
}

/** currentPassword is required for password accounts; Google-only accounts may omit it. */
export function updateProfile({ currentPassword, newUsername, newEmail, newPassword }) {
    return request('/auth/profile', {
        method: 'PUT',
        write: true,
        body: {
            current_password: currentPassword || null,
            new_username: newUsername || null,
            new_email: newEmail || null,
            new_password: newPassword || null,
        },
    });
}

export function uploadAvatar(file) {
    const formData = new FormData();
    formData.append('avatar', file);
    return request('/auth/avatar', { method: 'POST', write: true, body: formData });
}

/** Password accounts confirm with `password`; Google-only accounts with `confirmEmail`. */
export function deleteAccount({ password, confirmEmail }) {
    return request('/auth/account', {
        method: 'DELETE',
        write: true,
        body: { password: password || null, confirm_email: confirmEmail || null },
    });
}
