/** Display helpers shared by every page. */

/** ₹1,299 or ₹499.50 — Indian digit grouping, paise only when present. */
export function formatPrice(value) {
    const amount = Number(value) || 0;
    const hasPaise = Math.round(amount * 100) % 100 !== 0;
    return '₹' + amount.toLocaleString('en-IN', {
        minimumFractionDigits: hasPaise ? 2 : 0,
        maximumFractionDigits: 2,
    });
}

export function capitalize(text) {
    const s = String(text ?? '');
    return s.charAt(0).toUpperCase() + s.slice(1);
}

const COLOR_ALIASES = { 'navy blue': 'navy', grey: 'gray', beige: '#e8d9b5', mustard: '#d9a21b', maroon: '#7a1f2b' };

/** CSS colour for a product colour name, or null if the browser doesn't know it. */
export function swatchColor(name) {
    const key = String(name || '').trim().toLowerCase();
    const css = COLOR_ALIASES[key] || key.replace(/\s+/g, '');
    return css && window.CSS?.supports?.('color', css) ? css : null;
}

export function formatDate(iso) {
    const d = new Date(iso);
    return Number.isNaN(d.getTime())
        ? ''
        : d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
}
