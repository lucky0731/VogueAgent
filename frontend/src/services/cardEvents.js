import { handleAddToCartClick } from './cartActions.js';
import { toggleWish } from './wishlist.js';
import { mountHeader } from '../components/Header.js';
import { showToast } from '../utils/toast.js';

/**
 * Wire quick-add size buttons and wishlist hearts inside `root`.
 * `lookup(id)` returns the product for an id. Safe to call repeatedly: each
 * button is wired once. `onUnwish(id, card)` lets a page react (e.g. remove it).
 */
export function wireProductCards(root, lookup, { onUnwish } = {}) {
    root.querySelectorAll('.add-btn:not([data-wired])').forEach(btn => {
        btn.dataset.wired = '1';
        btn.addEventListener('click', () => {
            const product = lookup(btn.dataset.id);
            if (product) handleAddToCartClick(btn, { productId: product.id, name: product.name, size: btn.dataset.size || null });
        });
    });

    root.querySelectorAll('[data-wish]:not([data-wired])').forEach(btn => {
        btn.dataset.wired = '1';
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const product = lookup(btn.dataset.wish);
            const saved = toggleWish(btn.dataset.wish);
            btn.classList.toggle('on', saved);
            btn.setAttribute('aria-pressed', String(saved));
            btn.setAttribute('aria-label', `${saved ? 'Remove from' : 'Save to'} wishlist: ${product?.name || ''}`);
            showToast(saved ? `${product?.name || 'Item'} saved to your wishlist` : 'Removed from your wishlist', saved ? 'success' : 'info');
            mountHeader();
            if (!saved && onUnwish) onUnwish(btn.dataset.wish, btn.closest('.card'));
        });
    });
}
