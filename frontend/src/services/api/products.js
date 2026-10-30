import { request } from './http.js';

// Shares in-flight/resolved list fetches by query string, so pages asking for
// the same catalog view reuse one request. Cleared after any product write.
const productsCache = new Map();

export function invalidateProductsCache() {
    productsCache.clear();
}

/** Fetch products: { category, type, minPrice, maxPrice, q, sort } are all optional. */
export function fetchProducts({ category = '', type = '', minPrice = null, maxPrice = null, q = '', sort = 'newest' } = {}) {
    const params = new URLSearchParams();
    if (category) params.set('category', category);
    if (type) params.set('type', type);
    if (minPrice !== null && minPrice !== undefined) params.set('min_price', minPrice);
    if (maxPrice !== null && maxPrice !== undefined) params.set('max_price', maxPrice);
    if (q) params.set('q', q);
    if (sort && sort !== 'newest') params.set('sort', sort);
    const query = params.toString() ? `?${params}` : '';

    if (productsCache.has(query)) return productsCache.get(query);
    const promise = request(`/products${query}`).catch(err => {
        productsCache.delete(query);
        throw err;
    });
    productsCache.set(query, promise);
    return promise;
}

export function fetchProduct(id) {
    return request(`/products/${encodeURIComponent(id)}`);
}

async function productWrite(path, options) {
    const result = await request(path, { write: true, ...options });
    invalidateProductsCache();
    return result;
}

/** `formData` carries the fields and the image (multipart). */
export function addProduct(formData) {
    return productWrite('/products', { method: 'POST', body: formData });
}

export function updateProduct(id, formData) {
    return productWrite(`/products/${encodeURIComponent(id)}`, { method: 'PUT', body: formData });
}

export function deleteProduct(id) {
    return productWrite(`/products/${encodeURIComponent(id)}`, { method: 'DELETE' });
}

export function deleteAllProducts() {
    return productWrite('/products', { method: 'DELETE' });
}

/** Excel sheet + zip of images; the sheet's 'image' column names files in the zip. */
export function bulkUploadProducts(excelFile, zipFile) {
    const formData = new FormData();
    formData.append('excel_file', excelFile);
    formData.append('images_zip', zipFile);
    return productWrite('/products/bulk-upload', { method: 'POST', body: formData });
}
