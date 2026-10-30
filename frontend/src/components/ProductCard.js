import { escapeHtml } from '../utils/escapeHtml.js';
import { formatPrice, swatchColor } from '../utils/format.js';
import { PLACEHOLDER_IMAGE } from '../utils/placeholder.js';
import { isWished } from '../services/wishlist.js';

const HEART = '<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"><path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/></svg>';

/**
 * Photo-first product card. Hover (on hover-capable screens) reveals quick-add
 * size buttons; the heart saves to the wishlist; touch screens get a bag button
 * that opens the product page to pick a size.
 */
export function renderProductCard(p) {
  const id = escapeHtml(p.id);
  const sizes = Array.isArray(p.size) && p.size.length ? p.size : [];
  const colors = Array.isArray(p.color) ? p.color : [];
  const wished = isWished(p.id);
  return `
  <article class="card" data-id="${id}">
    <div class="card-media">
      <a class="card-img-link" href="#/product/${id}" tabindex="-1" aria-hidden="true">
        <img src="${escapeHtml(p.image || PLACEHOLDER_IMAGE)}" alt="" loading="lazy" />
      </a>
      <button class="wish-btn ${wished ? 'on' : ''}" data-wish="${id}" aria-pressed="${wished}" aria-label="${wished ? 'Remove from' : 'Save to'} wishlist: ${escapeHtml(p.name)}">${HEART}</button>
      <div class="quick-add" role="group" aria-label="Quick add ${escapeHtml(p.name)}">
        <span class="quick-label">Quick add</span>
        <div class="quick-sizes">
          ${(sizes.length ? sizes : [null]).map(s => `
            <button class="quick-size add-btn" data-id="${id}" data-size="${escapeHtml(s ?? '')}" data-busy-text="…" data-done-text="${s ? '✓' : 'Added'}" aria-label="${s ? `Add size ${escapeHtml(s)} to bag` : 'Add to bag'}">${s ? escapeHtml(s) : 'Add to bag'}</button>`).join('')}
        </div>
      </div>
      <a class="card-bag" href="#/product/${id}" aria-label="Choose size for ${escapeHtml(p.name)}">
        <svg aria-hidden="true" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M6 7h12l1 14H5L6 7z"/><path d="M9 7a3 3 0 0 1 6 0"/></svg>
      </a>
    </div>
    <div class="card-body">
      <h3 class="card-title"><a href="#/product/${id}">${escapeHtml(p.name)}</a></h3>
      <div class="card-meta">
        <span class="price">${formatPrice(p.price)}</span>
        <span class="dots" aria-label="Colours: ${escapeHtml(colors.join(', '))}">
          ${colors.slice(0, 4).map(c => {
            const css = swatchColor(c);
            return `<span class="dot" title="${escapeHtml(c)}" style="${css ? `background:${escapeHtml(css)}` : ''}"></span>`;
          }).join('')}
        </span>
      </div>
    </div>
  </article>`;
}
