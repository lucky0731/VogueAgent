/**
 * Hash-based navigation helpers, dependency-free so both the router and the
 * header can import them without a circular reference.
 */

/** Navigate to a hash route, e.g. navigate('#/cart'). Re-renders even if the hash is unchanged. */
export function navigate(path) {
    const target = path.startsWith('#') ? path : `#${path}`;
    if (window.location.hash === target || (!window.location.hash && target === '#/')) {
        window.dispatchEvent(new HashChangeEvent('hashchange'));
    } else {
        window.location.hash = target;
    }
}

/** "#/?cat=men&min=500" -> { path: '/', params: URLSearchParams } */
export function currentRoute() {
    const hash = window.location.hash.slice(1) || '/';
    const [path, query = ''] = hash.split('?');
    return { path: path || '/', params: new URLSearchParams(query) };
}
