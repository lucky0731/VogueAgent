import { state } from './state.js';
import { getCart } from './api/cart.js';
import { mountHeader } from '../components/Header.js';

/** The one place state.cartItemCount is written; repaints the header badge. */
export function setCartCount(count) {
    state.cartItemCount = Number(count) || 0;
    mountHeader();
}

/** Re-read the cart and update the badge. Never throws. */
export async function refreshCartCount() {
    if (!state.isLoggedIn) {
        setCartCount(0);
        return;
    }
    try {
        setCartCount((await getCart()).count);
    } catch (err) {
        console.error('Failed to refresh cart count:', err);
    }
}
