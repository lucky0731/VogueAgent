import { state, resetAdminForm } from '../../services/state.js';
import { addProduct, updateProduct } from '../../services/api_v2.js';
import { escapeHtml } from '../../utils/escapeHtml.js';
import { showToast } from '../../utils/toast.js';

const SIZES = ['XS', 'S', 'M', 'L', 'XL', 'XXL', 'One Size'];
const CATEGORIES = ['women', 'men', 'kids'];

export function renderProductForm() {
    const f = state.adminForm;
    const colorValue = Array.isArray(f.color) ? f.color.join(', ') : f.color || '';
    return `
    <section class="panel" id="productFormPanel">
      <h2>${state.isEditing ? `Edit “${escapeHtml(f.name)}”` : 'Add a product'}</h2>
      <form id="productForm" class="stack" novalidate>
        <label class="field"><span>Name</span>
          <input class="input" id="adminName" value="${escapeHtml(f.name)}" maxlength="120" /></label>
        <label class="field"><span>Description</span>
          <textarea class="input" id="adminDesc" rows="3" maxlength="2000">${escapeHtml(f.description)}</textarea></label>
        <label class="field"><span>Price (₹)</span>
          <input class="input" id="adminPrice" type="number" min="0" step="0.01" value="${escapeHtml(f.price ?? '')}" /></label>

        <fieldset class="picker">
          <legend>Category</legend>
          <div class="picker-options" id="adminCategoryButtons">
            ${CATEGORIES.map(cat => `
              <button type="button" class="size-opt ${f.category === cat ? 'active' : ''}" aria-pressed="${f.category === cat}" data-admin-cat="${cat}">${cat.charAt(0).toUpperCase() + cat.slice(1)}</button>`).join('')}
          </div>
        </fieldset>

        <fieldset class="picker">
          <legend>Sizes</legend>
          <div class="picker-options">
            ${SIZES.map(size => `
              <label class="check"><input type="checkbox" ${f.size?.includes(size) ? 'checked' : ''} data-size="${size}" /><span>${size}</span></label>`).join('')}
          </div>
        </fieldset>

        <label class="field"><span>Colours</span>
          <input class="input" id="adminColor" placeholder="Black, Blue, Red" value="${escapeHtml(colorValue)}" />
          <small>Separate colours with commas.</small></label>

        <label class="field"><span>${state.isEditing ? 'Replace image (optional)' : 'Image'}</span>
          <input type="file" accept="image/png, image/jpeg, image/webp, image/gif" id="adminImage" class="input" />
          <small>JPEG, PNG, WebP or GIF, up to 5 MB.</small></label>

        <div class="row">
          <button class="btn btn-primary" type="submit" id="${state.isEditing ? 'updateProductBtn' : 'addProductBtn'}">${state.isEditing ? 'Save product' : 'Add product'}</button>
          ${state.isEditing ? '<button type="button" id="cancelEditBtn" class="btn btn-ghost">Cancel</button>' : ''}
        </div>
      </form>
    </section>`;
}

export function setupProductFormEvents(rerender) {
    // Scoped to the form: the header's category links also use data attributes.
    document.querySelectorAll('#adminCategoryButtons [data-admin-cat]').forEach(btn => {
        btn.addEventListener('click', () => {
            collectInputs();
            state.adminForm.category = btn.dataset.adminCat;
            rerender();
        });
    });

    document.querySelectorAll('#productForm [data-size]').forEach(cb => {
        cb.addEventListener('change', () => {
            const current = state.adminForm.size || [];
            state.adminForm.size = cb.checked ? [...current, cb.dataset.size] : current.filter(s => s !== cb.dataset.size);
        });
    });

    document.getElementById('adminImage')?.addEventListener('change', (e) => {
        state.imageFile = e.target.files?.[0] || null;
    });

    document.getElementById('productForm')?.addEventListener('submit', (e) => {
        e.preventDefault();
        state.isEditing ? handleUpdateProduct(rerender) : handleAddProduct(rerender);
    });
    document.getElementById('cancelEditBtn')?.addEventListener('click', () => {
        resetAdminForm();
        rerender();
    });
}

/** Prepopulate the form for editing an existing product. */
export function editProduct(product, rerender) {
    state.isEditing = true;
    state.editId = product.id;
    state.imageFile = null;
    state.adminForm = {
        name: product.name,
        description: product.description,
        price: product.price,
        category: product.category,
        image: product.image,
        size: product.size || [],
        color: Array.isArray(product.color) ? product.color : String(product.color || '').split(',').map(c => c.trim()),
    };
    rerender().then(() => document.getElementById('productFormPanel')?.scrollIntoView({ behavior: 'smooth' }));
}

/** Copy typed values into state so a re-render (e.g. picking a category) doesn't lose them. */
function collectInputs() {
    const f = state.adminForm;
    f.name = document.getElementById('adminName').value.trim();
    f.description = document.getElementById('adminDesc').value.trim();
    f.price = document.getElementById('adminPrice').value;
    f.color = document.getElementById('adminColor').value.split(',').map(c => c.trim()).filter(Boolean);
}

function validate() {
    collectInputs();
    const f = state.adminForm;
    const price = Number(f.price);
    if (!f.name || !f.description || f.price === '' || Number.isNaN(price) || price < 0 || !f.category) {
        showToast('Fill in name, description, a valid price and a category.', 'info');
        return false;
    }
    if (!state.isEditing && !state.imageFile) {
        showToast('Choose an image for the new product.', 'info');
        return false;
    }
    return true;
}

function buildFormData() {
    const { name, description, price, category, size, color } = state.adminForm;
    const formData = new FormData();
    formData.append('name', name);
    formData.append('description', description);
    formData.append('price', String(Number(price)));
    formData.append('category', category);
    formData.append('size', size?.length ? size.join(',') : 'M,L');
    formData.append('color', color?.length ? color.join(',') : 'Black');
    if (state.imageFile) formData.append('image', state.imageFile);
    return formData;
}

async function handleAddProduct(rerender) {
    if (!validate()) return;
    try {
        await addProduct(buildFormData());
    } catch (err) {
        showToast(`Couldn't add product: ${err.message}`, 'error');
        return;
    }
    showToast(`${state.adminForm.name} added to the store`);
    resetAdminForm();
    rerender();
}

async function handleUpdateProduct(rerender) {
    if (!validate()) return;
    try {
        await updateProduct(state.editId, buildFormData());
    } catch (err) {
        showToast(`Couldn't save product: ${err.message}`, 'error');
        return;
    }
    showToast('Product saved');
    resetAdminForm();
    rerender();
}
