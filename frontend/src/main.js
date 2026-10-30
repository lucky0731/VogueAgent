import { router } from './router.js';
import { state, logout, setUser } from './services/state.js';
import { fetchProducts, getMe, initIngestionApiBase } from './services/api_v2.js';
import { refreshCartCount } from './services/cartCount.js';
import { mountFooter } from './components/Footer.js';
import { showToast } from './utils/toast.js';

window.addEventListener('hashchange', router);

// http.js fires this when the server rejects an expired/revoked token.
window.addEventListener('hem:logged-out', () => {
    showToast('Your session ended. Please log in again.', 'info');
    refreshCartCount();
});

window.addEventListener('DOMContentLoaded', async () => {
    mountFooter();
    // Resolve the API base, the logged-in user and the cart badge before the
    // first render — but always render, even if the backend is unreachable.
    try {
        await initIngestionApiBase();
        if (state.token) {
            try {
                setUser(await getMe());
            } catch (err) {
                if (err.status === 401) logout();
            }
        }
        // the catalogue feeds the header's menu photos; the shop still works without it
        const [products] = await Promise.all([fetchProducts().catch(() => []), refreshCartCount()]);
        state.allProducts = products;
    } catch (err) {
        console.error('Startup check failed:', err);
    }
    router();
});
