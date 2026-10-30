import { API_BASE, INGESTION_API_BASE } from './common.js';
import { state, logout } from '../state.js';

/**
 * The one fetch() wrapper the whole API layer goes through.
 *
 *   method - HTTP verb (default 'GET')
 *   body   - a plain object is sent as JSON; FormData is sent as-is
 *   write  - true routes the call to the ingestion service
 *
 * Adds `Authorization: Bearer <token>` when logged in. Resolves to the parsed
 * JSON body; throws Error(<readable message>) on failure. A 401 on a logged-in
 * request means the session expired, so the user is logged out.
 */
const REQUEST_TIMEOUT_MS = 20000;

function describe(detail, status) {
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail) && detail.length) {
        return detail.map(d => {
            const field = (d.loc || []).slice(-1)[0];
            return field ? `${field}: ${d.msg}` : d.msg;
        }).join('\n');
    }
    return `Request failed (${status})`;
}

export async function request(path, { method = 'GET', body, headers = {}, write = false } = {}) {
    const base = write ? INGESTION_API_BASE : API_BASE;
    const opts = { method, headers: { ...headers } };
    if (state.token) opts.headers.Authorization = `Bearer ${state.token}`;
    if (body instanceof FormData) {
        opts.body = body;
    } else if (body !== undefined) {
        opts.body = JSON.stringify(body);
        opts.headers['Content-Type'] = 'application/json';
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
    opts.signal = controller.signal;

    let res;
    try {
        res = await fetch(`${base}${path}`, opts);
    } catch (err) {
        if (err.name === 'AbortError') throw new Error('The server is taking too long to respond. Please try again.');
        throw new Error('Could not reach the server. Check your connection and try again.');
    } finally {
        clearTimeout(timeoutId);
    }

    const payload = await res.json().catch(() => null);
    if (!res.ok) {
        if (res.status === 401 && state.token) {
            logout();
            window.dispatchEvent(new CustomEvent('hem:logged-out'));
        }
        const error = new Error(describe(payload?.detail, res.status));
        error.status = res.status;
        throw error;
    }
    return payload;
}
