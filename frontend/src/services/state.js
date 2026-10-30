/**
 * Global application state.
 *
 * Login: the server returns a signed token, kept in localStorage and sent as
 * `Authorization: Bearer <token>` on every request (see services/api/http.js).
 * `state.user` is the profile from /auth/me, including `is_admin`.
 */
const TOKEN_KEY = 'hem_token';
const USER_KEY = 'hem_user';

function read(key) {
    try { return localStorage.getItem(key); } catch { return null; }
}
function write(key, value) {
    try {
        if (value == null) localStorage.removeItem(key);
        else localStorage.setItem(key, value);
    } catch { /* storage blocked: stay logged in for this tab only */ }
}
function readUser() {
    try { return JSON.parse(read(USER_KEY) || 'null'); } catch { return null; }
}

function emptyAdminForm() {
    return { name: '', description: '', price: '', category: 'men', image: '', size: [], color: [] };
}

function defaultUi() {
    return { profileEditOpen: false, profileDeleteOpen: false, authMode: 'login' };
}

export const state = {
    token: read(TOKEN_KEY),
    user: read(TOKEN_KEY) ? readUser() : null,

    get isLoggedIn() { return Boolean(this.token && this.user); },
    get isAdmin() { return Boolean(this.user?.is_admin); },
    get username() { return this.user?.username || ''; },
    get email() { return this.user?.email || ''; },

    cartItemCount: 0,

    // catalog filters (mirrored in the URL hash, see Home.js)
    filters: { category: '', min: null, max: null, q: '', sort: 'newest' },
    products: [],
    productList: [],

    // where to go after logging in (e.g. back to the product the user wanted)
    afterLogin: null,

    ui: defaultUi(),

    // admin product form
    isEditing: false,
    editId: null,
    adminForm: emptyAdminForm(),
    imageFile: null,
};

/** Store the token + profile returned by /auth/login, /auth/register, /auth/google. */
export function login(authResponse) {
    const { token, message, ...user } = authResponse;
    if (token) {
        state.token = token;
        write(TOKEN_KEY, token);
    }
    setUser(user);
}

/** Replace the cached profile (e.g. after /auth/me or an avatar change). */
export function setUser(user) {
    state.user = user;
    write(USER_KEY, user ? JSON.stringify({ ...user, avatar: null }) : null);
}

export function logout() {
    state.token = null;
    state.user = null;
    state.cartItemCount = 0;
    write(TOKEN_KEY, null);
    write(USER_KEY, null);
}

export function resetTransientUi() {
    state.ui = defaultUi();
}

export function resetAdminForm() {
    state.isEditing = false;
    state.editId = null;
    state.imageFile = null;
    state.adminForm = emptyAdminForm();
}
