import { state } from '../services/state.js';
import { getCart, updateCartItem, removeCartItem, clearCart, checkout } from '../services/api_v2.js';
import { setCartCount } from '../services/cartCount.js';
import { navigate } from '../services/nav.js';
import { escapeHtml } from '../utils/escapeHtml.js';
import { formatPrice } from '../utils/format.js';
import { PLACEHOLDER_IMAGE } from '../utils/placeholder.js';
import { showToast } from '../utils/toast.js';

const MAX_QTY = 20;

export async function renderCart() {
    const app = document.getElementById('app');
    if (!state.isLoggedIn) {
        app.innerHTML = `
        <div class="container page empty-state">
          <h1>Your bag</h1>
          <p>Log in to see your bag — it's saved to your account, so it follows you across devices.</p>
          <a href="#/profile" class="btn btn-primary" id="loginForBag">Log in</a>
        </div>`;
        document.getElementById('loginForBag').addEventListener('click', () => { state.afterLogin = '#/cart'; });
        return;
    }

    app.innerHTML = `<div class="container page"><h1 class="page-title">Your bag</h1><p class="loading">Loading your bag…</p></div>`;
    let cart;
    try {
        cart = await getCart();
    } catch (err) {
        app.innerHTML = `<div class="container page empty-state"><h1>Your bag</h1><p>${escapeHtml(err.message)}</p></div>`;
        return;
    }
    paint(cart);
}

function paint(cart) {
    setCartCount(cart.count);
    const app = document.getElementById('app');

    if (!cart.items.length) {
        app.innerHTML = `
        <div class="container page empty-state">
          <h1>Your bag is empty</h1>
          <p>Add something you love — sizes and colours are chosen on each product page.</p>
          <a href="#/" class="btn btn-primary">Start shopping</a>
        </div>`;
        return;
    }

    const unavailable = cart.items.filter(i => !i.available);
    app.innerHTML = `
    <div class="container page">
      <h1 class="page-title">Your bag <span class="muted">(${cart.count} ${cart.count === 1 ? 'item' : 'items'})</span></h1>
      <div class="bag">
        <ul class="bag-lines">
          ${cart.items.map(renderLine).join('')}
        </ul>
        <aside class="summary panel" aria-label="Order summary">
          <h2>Order summary</h2>
          <dl>
            <div><dt>Subtotal</dt><dd>${formatPrice(cart.subtotal)}</dd></div>
            <div><dt>Delivery</dt><dd class="good">Free</dd></div>
            <div class="total"><dt>Total</dt><dd>${formatPrice(cart.subtotal)}</dd></div>
          </dl>
          ${unavailable.length ? `<p class="warn">Remove the ${unavailable.length === 1 ? 'item' : 'items'} marked “No longer available” to check out.</p>` : ''}
          <button id="checkoutBtn" class="btn btn-primary btn-block btn-lg" ${unavailable.length ? 'disabled' : ''}>Place order</button>
          <a href="#/" class="btn btn-ghost btn-block">Keep shopping</a>
          <button id="clearCartBtn" class="link-danger">Empty bag</button>
        </aside>
      </div>
    </div>`;
    wire(cart);
}

function renderLine(item) {
    const variant = [item.size && `Size ${item.size}`, item.color].filter(Boolean).join(' · ');
    return `
    <li class="bag-line ${item.available ? '' : 'is-gone'}" data-item="${escapeHtml(item.item_id)}">
      <a href="${item.available ? `#/product/${escapeHtml(item.product_id)}` : '#/cart'}" class="bag-img">
        <img src="${escapeHtml(item.image || PLACEHOLDER_IMAGE)}" alt="" loading="lazy" />
      </a>
      <div class="bag-info">
        <h3>${escapeHtml(item.name)}</h3>
        ${variant ? `<p class="muted">${escapeHtml(variant)}</p>` : ''}
        ${item.available ? `<p class="muted">${formatPrice(item.price)} each</p>` : `<p class="warn">No longer available</p>`}
        <div class="bag-controls">
          ${item.available ? `
          <div class="stepper stepper-sm" role="group" aria-label="Quantity of ${escapeHtml(item.name)}">
            <button type="button" data-act="dec" aria-label="Decrease" ${item.quantity <= 1 ? 'disabled' : ''}>−</button>
            <output>${item.quantity}</output>
            <button type="button" data-act="inc" aria-label="Increase" ${item.quantity >= MAX_QTY ? 'disabled' : ''}>+</button>
          </div>` : ''}
          <button type="button" class="link-danger" data-act="remove">Remove</button>
        </div>
      </div>
      <p class="bag-total">${item.available ? formatPrice(item.line_total) : ''}</p>
    </li>`;
}

function wire(cart) {
    document.querySelectorAll('.bag-line').forEach(line => {
        const item = cart.items.find(i => i.item_id === line.dataset.item);
        line.querySelectorAll('[data-act]').forEach(btn => btn.addEventListener('click', async () => {
            btn.disabled = true;
            try {
                const act = btn.dataset.act;
                const next = act === 'remove'
                    ? await removeCartItem(item.item_id)
                    : await updateCartItem(item.item_id, item.quantity + (act === 'inc' ? 1 : -1));
                if (act === 'remove') showToast(`${item.name} removed`);
                paint(next);
            } catch (err) {
                showToast(err.message, 'error');
                btn.disabled = false;
            }
        }));
    });

    document.getElementById('clearCartBtn')?.addEventListener('click', async () => {
        if (!confirm('Remove everything from your bag?')) return;
        try {
            paint(await clearCart());
        } catch (err) {
            showToast(err.message, 'error');
        }
    });

    document.getElementById('checkoutBtn')?.addEventListener('click', async (e) => {
        const btn = e.currentTarget;
        btn.disabled = true;
        btn.textContent = 'Placing order…';
        try {
            const result = await checkout();
            setCartCount(0);
            showToast(`Order placed — ${formatPrice(result.total)}. Thank you!`);
            navigate('#/profile');
        } catch (err) {
            showToast(err.message, 'error');
            btn.disabled = false;
            btn.textContent = 'Place order';
        }
    });
}
