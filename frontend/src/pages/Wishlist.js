import { state } from '../services/state.js';
import { fetchProducts } from '../services/api_v2.js';
import { wishlistIds } from '../services/wishlist.js';
import { wireProductCards } from '../services/cardEvents.js';
import { renderProductCard } from '../components/ProductCard.js';
import { escapeHtml } from '../utils/escapeHtml.js';

/** Saved products (kept in this browser). */
export async function renderWishlist() {
    const app = document.getElementById('app');
    app.innerHTML = `<div class="container page"><p class="loading">Loading your wishlist…</p></div>`;
    let all;
    try {
        all = state.allProducts?.length ? state.allProducts : await fetchProducts();
        state.allProducts = all;
    } catch (err) {
        app.innerHTML = `<div class="container page empty-state"><h1>Wishlist</h1><p>${escapeHtml(err.message)}</p></div>`;
        return;
    }
    const ids = wishlistIds();
    const saved = all.filter(p => ids.has(p.id));

    if (!saved.length) {
        app.innerHTML = `
        <div class="container page empty-state">
          <h1>Your wishlist is empty</h1>
          <p>Tap the heart on any piece to save it here for later.</p>
          <a class="btn btn-primary" href="#/?all=1">Browse new in</a>
        </div>`;
        return;
    }

    app.innerHTML = `
    <section class="listing-head"><div class="container">
      <nav class="crumbs" aria-label="Breadcrumb"><a href="#/">Home</a><span aria-hidden="true">/</span><span>Wishlist</span></nav>
      <h1>Wishlist</h1><p>${saved.length} saved ${saved.length === 1 ? 'piece' : 'pieces'}. Hover a photo to add your size to the bag.</p>
    </div></section>
    <section class="catalog container"><div class="grid" id="productGrid">${saved.map(renderProductCard).join('')}</div></section>`;

    wireProductCards(app, id => all.find(p => p.id === id), {
        onUnwish: (_id, card) => {
            card?.remove();
            if (!app.querySelector('.card')) renderWishlist();
        },
    });
}
