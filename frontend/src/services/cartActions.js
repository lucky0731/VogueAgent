import { state } from './state.js';
import { addToCart } from './api/cart.js';
import { setCartCount } from './cartCount.js';
import { navigate } from './nav.js';
import { showToast } from '../utils/toast.js';

/** Send a guest to the login page, remembering where to come back to. */
export function requireLogin(message = 'Log in to add items to your bag.') {
    if (state.isLoggedIn) return true;
    state.afterLogin = window.location.hash || '#/';
    showToast(message, 'info');
    navigate('#/profile');
    return false;
}

/**
 * Shared "Add to bag" behaviour: disables the button, calls the API, updates
 * the badge, and briefly shows a success state.
 */
export async function handleAddToCartClick(buttonEl, { productId, name, size = null, color = null, quantity = 1 }) {
    if (!requireLogin()) return false;
    const originalText = buttonEl.textContent;
    buttonEl.disabled = true;
    buttonEl.textContent = buttonEl.dataset.busyText || 'Adding…';
    try {
        const cart = await addToCart({ productId, quantity, size, color });
        setCartCount(cart.count);
        buttonEl.textContent = buttonEl.dataset.doneText || 'Added to bag';
        buttonEl.classList.add('is-done');
        showToast(`${name}${size ? ` (${size})` : ''} added to your bag`);
        setTimeout(() => {
            buttonEl.disabled = false;
            buttonEl.textContent = originalText;
            buttonEl.classList.remove('is-done');
        }, 1600);
        return true;
    } catch (err) {
        showToast(err.message, 'error');
        buttonEl.disabled = false;
        buttonEl.textContent = originalText;
        return false;
    }
}
