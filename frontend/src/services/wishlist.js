/**
 * Wishlist: product ids saved in this browser (localStorage). It's a per-device
 * convenience — no account needed — so failures to read/write are ignored.
 */
const KEY = 'hem_wishlist';
const listeners = new Set();

function read() {
    try { return new Set(JSON.parse(localStorage.getItem(KEY) || '[]')); } catch { return new Set(); }
}
function write(ids) {
    try { localStorage.setItem(KEY, JSON.stringify([...ids])); } catch { /* storage blocked */ }
}

export function wishlistIds() {
    return read();
}

export function isWished(id) {
    return read().has(id);
}

/** Toggle a product; returns true if it is now saved. */
export function toggleWish(id) {
    const ids = read();
    const saved = !ids.has(id);
    saved ? ids.add(id) : ids.delete(id);
    write(ids);
    listeners.forEach(fn => fn(ids.size));
    return saved;
}

export function wishlistCount() {
    return read().size;
}

export function onWishlistChange(fn) {
    listeners.add(fn);
}
