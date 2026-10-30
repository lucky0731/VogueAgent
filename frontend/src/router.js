import { renderHome } from './pages/Home.js';
import { renderAdmin } from './pages/Admin.js';
import { renderProductDetail } from './pages/ProductDetail.js';
import { renderCart } from './pages/Cart.js';
import { renderProfile } from './pages/Profile.js';
import { renderWishlist } from './pages/Wishlist.js';
import { mountHeader, resetHeaderSearch } from './components/Header.js';
import { state, resetTransientUi } from './services/state.js';
import { navigate, currentRoute } from './services/nav.js';
import { showToast } from './utils/toast.js';

let lastPath = null;

export async function router() {
    const { path } = currentRoute();

    // Reset per-page toggles when the page changes (not on in-page re-renders
    // such as a filter change, which keep the same path).
    const pageChanged = path !== lastPath;
    if (pageChanged) {
        resetTransientUi();
        resetHeaderSearch();
        lastPath = path;
    }

    mountHeader();

    if (path === '/add-products' || path === '/admin') {
        if (!state.isAdmin) {
            showToast('That page is for store admins only.', 'error');
            navigate('#/');
            return;
        }
        await renderAdmin();
    } else if (path === '/cart') {
        await renderCart();
    } else if (path === '/wishlist') {
        await renderWishlist();
    } else if (path === '/profile') {
        await renderProfile();
    } else if (path.startsWith('/product/')) {
        await renderProductDetail(decodeURIComponent(path.split('/')[2] || ''));
    } else {
        await renderHome({ pageChanged });
    }
    mountHeader(); // pages may update filters/state the header reflects
    if (pageChanged) window.scrollTo({ top: 0 });
}
