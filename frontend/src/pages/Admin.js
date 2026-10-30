import { state } from '../services/state.js';
import { fetchProducts } from '../services/api_v2.js';
import { renderQuickActions, setupQuickActionsEvents } from './admin/quickActions.js';
import { renderBulkImport, setupBulkImportEvents } from './admin/bulkImport.js';
import { renderProductForm, setupProductFormEvents } from './admin/productForm.js';
import { renderProductList, setupProductListEvents } from './admin/productList.js';

/** Admin dashboard: add, edit, bulk-import and delete products. */
export async function renderAdmin() {
    try {
        state.productList = await fetchProducts();
    } catch (err) {
        console.error('Failed to load products:', err);
        state.productList = [];
    }

    document.getElementById('app').innerHTML = `
    <div class="container page admin">
      ${renderQuickActions()}
      <div class="admin-grid">
        ${renderProductForm()}
        ${renderBulkImport()}
      </div>
      ${renderProductList()}
    </div>`;

    setupQuickActionsEvents(renderAdmin);
    setupBulkImportEvents(renderAdmin);
    setupProductFormEvents(renderAdmin);
    setupProductListEvents(renderAdmin);
}
