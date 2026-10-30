import { request } from './http.js';

/** Turn the whole cart into one order (prices are set by the server). */
export function checkout() {
    return request('/orders/checkout', { method: 'POST', write: true });
}

/** Order one product straight from its page. */
export function buyNow({ productId, quantity = 1, size = null, color = null }) {
    return request('/orders', {
        method: 'POST',
        write: true,
        body: { product_id: productId, quantity, size, color },
    });
}

export function getOrderHistory() {
    return request('/orders');
}
