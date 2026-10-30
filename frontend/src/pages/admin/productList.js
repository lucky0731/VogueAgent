import { state } from '../../services/state.js';
import { deleteProduct } from '../../services/api_v2.js';
import { escapeHtml } from '../../utils/escapeHtml.js';
import { capitalize, formatPrice } from '../../utils/format.js';
import { PLACEHOLDER_IMAGE } from '../../utils/placeholder.js';
import { showToast } from '../../utils/toast.js';
import { editProduct } from './productForm.js';

export function renderProductList() {
    return `
    <section class="admin-list" aria-labelledby="adminListTitle">
      <h2 id="adminListTitle">All products</h2>
      ${state.productList.length === 0 ? '<p class="muted">No products yet. Add one above or use bulk import.</p>' : `
      <div class="table-wrap">
        <table class="table">
          <thead><tr><th>Product</th><th>Category</th><th>Price</th><th>Sizes</th><th><span class="sr-only">Actions</span></th></tr></thead>
          <tbody>
            ${state.productList.map(p => `
            <tr>
              <td><div class="table-product"><img src="${escapeHtml(p.image || PLACEHOLDER_IMAGE)}" alt="" loading="lazy" /><a href="#/product/${escapeHtml(p.id)}">${escapeHtml(p.name)}</a></div></td>
              <td><span class="tag tag-${escapeHtml(p.category)}">${escapeHtml(capitalize(p.category))}</span></td>
              <td>${formatPrice(p.price)}</td>
              <td>${escapeHtml(p.size?.join(', ') || '—')}</td>
              <td class="table-actions">
                <button class="btn btn-small btn-outline edit-btn" data-id="${escapeHtml(p.id)}">Edit</button>
                <button class="btn btn-small btn-ghost delete-btn" data-id="${escapeHtml(p.id)}">Delete</button>
              </td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>`}
    </section>`;
}

export function setupProductListEvents(rerender) {
    document.querySelectorAll('.edit-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const product = state.productList.find(p => p.id === btn.dataset.id);
            if (product) editProduct(product, rerender);
        });
    });
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const product = state.productList.find(p => p.id === btn.dataset.id);
            if (!confirm(`Delete “${product?.name}”? This cannot be undone.`)) return;
            try {
                await deleteProduct(btn.dataset.id);
                showToast('Product deleted', 'info');
                rerender();
            } catch (err) {
                showToast(`Couldn't delete: ${err.message}`, 'error');
            }
        });
    });
}
