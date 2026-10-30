import { state } from '../services/state.js';
import { fetchProduct, fetchProducts, buyNow } from '../services/api_v2.js';
import { handleAddToCartClick, requireLogin } from '../services/cartActions.js';
import { wireProductCards } from '../services/cardEvents.js';
import { isWished } from '../services/wishlist.js';
import { renderProductCard } from '../components/ProductCard.js';
import { navigate } from '../services/nav.js';
import { escapeHtml } from '../utils/escapeHtml.js';
import { capitalize, formatPrice, swatchColor } from '../utils/format.js';
import { PLACEHOLDER_IMAGE } from '../utils/placeholder.js';
import { showToast } from '../utils/toast.js';

const MAX_QTY = 20;

export async function renderProductDetail(id) {
    const app = document.getElementById('app');
    app.innerHTML = `<div class="container page"><p class="loading">Loading…</p></div>`;

    let product;
    try {
        product = await fetchProduct(id);
    } catch (err) {
        app.innerHTML = `
        <div class="container page empty-state">
          <h1>We couldn't find that product</h1>
          <p>It may have sold out or been removed from the store.</p>
          <a href="#/" class="btn btn-primary">Browse all products</a>
        </div>`;
        return;
    }

    const sizes = Array.isArray(product.size) ? product.size : [];
    const colors = Array.isArray(product.color) ? product.color : [];
    const choice = { size: sizes.length === 1 ? sizes[0] : null, color: colors[0] || null, quantity: 1 };

    let related = [];
    try {
        related = (await fetchProducts({ category: product.category })).filter(p => p.id !== product.id).slice(0, 4);
    } catch { /* optional section */ }

    app.innerHTML = `
    <div class="container page">
      <nav class="crumbs" aria-label="Breadcrumb">
        <a href="#/">Home</a><span aria-hidden="true">/</span>
        <a href="#/?cat=${escapeHtml(product.category)}">${escapeHtml(capitalize(product.category))}</a><span aria-hidden="true">/</span>
        <span>${escapeHtml(product.name)}</span>
      </nav>
      <div class="pdp">
        <div class="pdp-media">
          <img src="${escapeHtml(product.image || PLACEHOLDER_IMAGE)}" alt="${escapeHtml(product.name)}" />
        </div>
        <div class="pdp-info">
          <span class="tag tag-${escapeHtml(product.category)}">${escapeHtml(capitalize(product.category))}</span>
          <h1>${escapeHtml(product.name)}</h1>
          <p class="pdp-price">${formatPrice(product.price)} <span>Inclusive of all taxes</span></p>
          <p class="pdp-desc">${escapeHtml(product.description)}</p>

          ${sizes.length ? `
          <fieldset class="picker">
            <legend>Size <span class="picked" id="pickedSize">${choice.size ? escapeHtml(choice.size) : 'Choose a size'}</span></legend>
            <div class="picker-options">
              ${sizes.map(s => `<button type="button" class="size-opt ${choice.size === s ? 'active' : ''}" aria-pressed="${choice.size === s}" data-size="${escapeHtml(s)}">${escapeHtml(s)}</button>`).join('')}
            </div>
          </fieldset>` : ''}

          ${colors.length ? `
          <fieldset class="picker">
            <legend>Colour <span class="picked" id="pickedColor">${escapeHtml(choice.color || '')}</span></legend>
            <div class="picker-options">
              ${colors.map(c => {
                  const css = swatchColor(c);
                  return `<button type="button" class="color-opt ${choice.color === c ? 'active' : ''}" aria-pressed="${choice.color === c}" data-color="${escapeHtml(c)}" title="${escapeHtml(c)}">
                    <span class="dot" style="${css ? `background:${escapeHtml(css)}` : ''}"></span>${escapeHtml(c)}</button>`;
              }).join('')}
            </div>
          </fieldset>` : ''}

          <div class="picker">
            <span class="legend-like" id="qtyLabel">Quantity</span>
            <div class="stepper" role="group" aria-labelledby="qtyLabel">
              <button type="button" id="qtyDown" aria-label="Decrease quantity">−</button>
              <output id="qtyValue">1</output>
              <button type="button" id="qtyUp" aria-label="Increase quantity">+</button>
            </div>
          </div>

          <div class="pdp-actions">
            <button class="btn btn-primary btn-lg" id="btnAddToCart">Add to bag</button>
            <div class="pdp-actions-row">
              <button class="btn btn-outline btn-lg" id="btnBuyNow">Buy now</button>
              <button class="btn btn-outline btn-lg wish-btn-lg ${isWished(product.id) ? 'on' : ''}" data-wish="${escapeHtml(product.id)}" aria-pressed="${isWished(product.id)}" aria-label="Save to wishlist: ${escapeHtml(product.name)}">
                <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"><path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/></svg>
                <span>Wishlist</span>
              </button>
            </div>
          </div>

          <dl class="pdp-details">
            <div><dt>Category</dt><dd>${escapeHtml(capitalize(product.category))}</dd></div>
            ${sizes.length ? `<div><dt>Sizes</dt><dd>${escapeHtml(sizes.join(', '))}</dd></div>` : ''}
            ${colors.length ? `<div><dt>Colours</dt><dd>${escapeHtml(colors.join(', '))}</dd></div>` : ''}
            <div><dt>Delivery</dt><dd>Free, in 3–7 working days</dd></div>
            <div><dt>Returns</dt><dd>Within 7 days, unworn with tags</dd></div>
          </dl>
        </div>
      </div>

      ${related.length ? `
      <section class="related" aria-labelledby="relatedTitle">
        <h2 id="relatedTitle">You may also like</h2>
        <div class="grid">${related.map(renderProductCard).join('')}</div>
      </section>` : ''}
    </div>`;

    // --- pickers -----------------------------------------------------------
    app.querySelectorAll('.size-opt').forEach(btn => btn.addEventListener('click', () => {
        choice.size = btn.dataset.size;
        app.querySelectorAll('.size-opt').forEach(b => {
            b.classList.toggle('active', b === btn);
            b.setAttribute('aria-pressed', String(b === btn));
        });
        document.getElementById('pickedSize').textContent = choice.size;
    }));
    app.querySelectorAll('.color-opt').forEach(btn => btn.addEventListener('click', () => {
        choice.color = btn.dataset.color;
        app.querySelectorAll('.color-opt').forEach(b => {
            b.classList.toggle('active', b === btn);
            b.setAttribute('aria-pressed', String(b === btn));
        });
        document.getElementById('pickedColor').textContent = choice.color;
    }));
    const qtyOut = document.getElementById('qtyValue');
    document.getElementById('qtyDown').addEventListener('click', () => {
        choice.quantity = Math.max(1, choice.quantity - 1);
        qtyOut.textContent = choice.quantity;
    });
    document.getElementById('qtyUp').addEventListener('click', () => {
        choice.quantity = Math.min(MAX_QTY, choice.quantity + 1);
        qtyOut.textContent = choice.quantity;
    });

    const needsSize = () => {
        if (sizes.length && !choice.size) {
            showToast('Choose a size first.', 'info');
            app.querySelector('.size-opt')?.focus();
            return true;
        }
        return false;
    };

    // --- actions -----------------------------------------------------------
    document.getElementById('btnAddToCart').addEventListener('click', (e) => {
        if (needsSize()) return;
        handleAddToCartClick(e.currentTarget, {
            productId: product.id, name: product.name, size: choice.size, color: choice.color, quantity: choice.quantity,
        });
    });

    document.getElementById('btnBuyNow').addEventListener('click', async (e) => {
        if (needsSize() || !requireLogin('Log in to place your order.')) return;
        const btn = e.currentTarget;
        btn.disabled = true;
        btn.textContent = 'Placing order…';
        try {
            const result = await buyNow({ productId: product.id, size: choice.size, color: choice.color, quantity: choice.quantity });
            showToast(`Order placed — ${formatPrice(result.total)}. See it in your orders.`);
            navigate('#/profile');
        } catch (err) {
            showToast(err.message, 'error');
            btn.disabled = false;
            btn.textContent = 'Buy now';
        }
    });

    // related cards + the wishlist button on this page
    wireProductCards(app, id => (id === product.id ? product : related.find(x => x.id === id)));
}
