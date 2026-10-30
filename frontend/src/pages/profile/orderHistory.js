import { escapeHtml } from '../../utils/escapeHtml.js';
import { formatDate, formatPrice } from '../../utils/format.js';
import { PLACEHOLDER_IMAGE } from '../../utils/placeholder.js';

/** Read-only order list — one card per order, with its line items. */
export function renderOrderHistory(orders) {
    return `
    <section class="panel">
      <h2>Your orders</h2>
      ${orders.length === 0 ? `
        <div class="empty-state small">
          <p>No orders yet. When you place one, it shows up here with every item and the total paid.</p>
          <a href="#/" class="btn btn-outline">Start shopping</a>
        </div>` : `
        <ol class="orders">
          ${orders.map(o => `
          <li class="order">
            <div class="order-head">
              <div>
                <p class="order-id">Order #${escapeHtml(String(o.id).slice(-6).toUpperCase())}</p>
                <p class="muted">${escapeHtml(formatDate(o.created_at))} · ${o.item_count} ${o.item_count === 1 ? 'item' : 'items'}</p>
              </div>
              <div class="order-right">
                <span class="status">${escapeHtml(o.status || 'placed')}</span>
                <p class="order-total">${formatPrice(o.total)}</p>
              </div>
            </div>
            <ul class="order-items">
              ${(o.items || []).map(i => `
              <li>
                <img src="${escapeHtml(i.image || PLACEHOLDER_IMAGE)}" alt="" loading="lazy" />
                <span>${escapeHtml(i.name)}${i.size ? ` · ${escapeHtml(i.size)}` : ''}${i.color ? ` · ${escapeHtml(i.color)}` : ''}</span>
                <span class="muted">${i.quantity} × ${formatPrice(i.price)}</span>
              </li>`).join('')}
            </ul>
          </li>`).join('')}
        </ol>`}
    </section>`;
}
