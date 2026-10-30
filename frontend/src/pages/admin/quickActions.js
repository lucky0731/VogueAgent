import { state } from '../../services/state.js';
import { deleteAllProducts } from '../../services/api_v2.js';
import { showToast } from '../../utils/toast.js';

export function renderQuickActions() {
    return `
    <div class="admin-head">
      <div>
        <h1 class="page-title">Manage store</h1>
        <p class="muted">${state.productList.length} products live. Changes show in the shop straight away.</p>
      </div>
      <button id="deleteAllBtn" class="btn btn-outline btn-danger-outline">Delete all products</button>
    </div>`;
}

export function setupQuickActionsEvents(rerender) {
    document.getElementById('deleteAllBtn')?.addEventListener('click', async () => {
        if (!confirm('Delete EVERY product in the store? This cannot be undone.')) return;
        const btn = document.getElementById('deleteAllBtn');
        btn.textContent = 'Deleting…';
        btn.disabled = true;
        try {
            const result = await deleteAllProducts();
            showToast(result.message, 'info');
            rerender();
        } catch (e) {
            showToast(`Couldn't delete products: ${e.message}`, 'error');
            btn.textContent = 'Delete all products';
            btn.disabled = false;
        }
    });
}
