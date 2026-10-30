import { request } from './http.js';

// Every cart call returns the whole cart: { items, subtotal, count }.

export function getCart() {
    return request('/cart');
}

export function addToCart({ productId, quantity = 1, size = null, color = null }) {
    return request('/cart/items', {
        method: 'POST',
        write: true,
        body: { product_id: productId, quantity, size, color },
    });
}

export function updateCartItem(itemId, quantity) {
    return request(`/cart/items/${encodeURIComponent(itemId)}`, { method: 'PATCH', write: true, body: { quantity } });
}

export function removeCartItem(itemId) {
    return request(`/cart/items/${encodeURIComponent(itemId)}`, { method: 'DELETE', write: true });
}

export function clearCart() {
    return request('/cart', { method: 'DELETE', write: true });
}
