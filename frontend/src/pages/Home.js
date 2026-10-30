import { state } from '../services/state.js';
import { fetchProducts } from '../services/api_v2.js';
import { wireProductCards } from '../services/cardEvents.js';
import { renderHero } from '../components/Hero.js';
import { renderProductCard } from '../components/ProductCard.js';
import { navigate, currentRoute } from '../services/nav.js';
import { escapeHtml } from '../utils/escapeHtml.js';
import { capitalize, formatPrice } from '../utils/format.js';
import { HOME_TYPES, MENU, OCCASION, matchesType, typeHref, typeLabel } from '../utils/catalogTypes.js';
import { PLACEHOLDER_IMAGE } from '../utils/placeholder.js';

const PRICE_RANGES = [
    { label: 'Any price', min: null, max: null },
    { label: 'Under ₹500', min: null, max: 500 },
    { label: '₹500 – ₹1,000', min: 500, max: 1000 },
    { label: '₹1,000 – ₹2,000', min: 1000, max: 2000 },
    { label: '₹2,000 – ₹5,000', min: 2000, max: 5000 },
    { label: 'Above ₹5,000', min: 5000, max: null },
];

const SORTS = [
    { value: 'newest', label: 'Newest first' },
    { value: 'price_asc', label: 'Price: low to high' },
    { value: 'price_desc', label: 'Price: high to low' },
    { value: 'name', label: 'Name: A to Z' },
];

const PAGE_SIZE = 24;
let visible = PAGE_SIZE;
let lastFilterKey = null;

/** The catalogue view lives in the hash: #/?cat=men&type=Shirt&min=500&max=1000&q=…&sort=…&all=1 */
function readFilters() {
    const { params } = currentRoute();
    const num = key => (params.has(key) && params.get(key) !== '' ? Number(params.get(key)) : null);
    return {
        category: params.get('cat') || '',
        type: params.get('type') || '',
        min: num('min'),
        max: num('max'),
        q: (params.get('q') || '').trim(),
        sort: params.get('sort') || 'newest',
        all: params.get('all') === '1',
    };
}

function filterHash(overrides = {}) {
    const f = { ...state.filters, ...overrides };
    const params = new URLSearchParams();
    if (f.category) params.set('cat', f.category);
    if (f.type) params.set('type', f.type);
    if (f.min != null) params.set('min', f.min);
    if (f.max != null) params.set('max', f.max);
    if (f.q) params.set('q', f.q);
    if (f.sort && f.sort !== 'newest') params.set('sort', f.sort);
    if (!params.toString() && f.all) params.set('all', '1'); // stay on the full catalogue
    return params.toString() ? `#/?${params}` : '#/';
}

const lookup = id => (state.allProducts || []).find(p => p.id === id) || state.products.find(p => p.id === id);

export async function renderHome({ pageChanged = true } = {}) {
    state.filters = readFilters();
    const f = state.filters;
    const isLanding = !f.all && !f.category && !f.type && f.min == null && f.max == null && !f.q && f.sort === 'newest';
    const app = document.getElementById('app');
    if (pageChanged) app.innerHTML = `<div class="container page"><p class="loading">Loading the collection…</p></div>`;

    let all = [];
    let products = [];
    try {
        [all, products] = await Promise.all([
            fetchProducts(),
            fetchProducts({ category: f.category, type: f.type, minPrice: f.min, maxPrice: f.max, q: f.q, sort: f.sort }),
        ]);
    } catch (err) {
        app.innerHTML = `
        <div class="container page empty-state">
          <h1>We couldn't load the shop</h1>
          <p>${escapeHtml(err.message)}</p>
          <button class="btn btn-primary" id="retryBtn">Try again</button>
        </div>`;
        document.getElementById('retryBtn').addEventListener('click', () => renderHome());
        return;
    }
    state.products = products;
    state.allProducts = all;

    const filterKey = filterHash();
    if (filterKey !== lastFilterKey) {
        visible = PAGE_SIZE;
        lastFilterKey = filterKey;
    }

    app.innerHTML = isLanding
        ? renderHero(all)
          + renderTypeTiles(all)
          + renderNewIn(all)
          + renderCampaigns(all)
          + renderEdit(all)
          + renderServices()
        : renderListingHeader(f, products.length) + renderCatalog(f, products);

    wireHomeEvents();
    if (!isLanding && !pageChanged) document.getElementById('catalog')?.scrollIntoView({ block: 'start' });
}

/* ---------- landing sections ---------- */

function sectionHead(title, link) {
    return `<div class="section-head"><h2>${title}</h2>${link ? `<a class="text-link" href="${link.href}">${link.label}</a>` : ''}</div>`;
}

function renderTypeTiles(all) {
    const used = new Set();
    const tiles = HOME_TYPES.map(t => {
        const items = all.filter(p => p.image && matchesType(p, t.match));
        const cover = items.find(p => !used.has(p.id)) || items[0];
        if (cover) used.add(cover.id);
        return { ...t, cover, count: items.length };
    }).filter(t => t.count);
    return `
    <section class="container section" aria-labelledby="typesTitle">
      <div class="section-head center"><h2 id="typesTitle">Shop by category</h2></div>
      <div class="type-tiles">
        ${tiles.map(t => `
        <a class="type-tile" href="${typeHref(t.match)}">
          <span class="type-img"><img src="${escapeHtml(t.cover?.image || PLACEHOLDER_IMAGE)}" alt="" loading="lazy" /></span>
          <span class="type-label">${t.label}</span>
        </a>`).join('')}
      </div>
    </section>`;
}

function renderNewIn(all) {
    const items = all.slice(0, 12);
    if (!items.length) return '';
    return `
    <section class="section new-in" aria-labelledby="newTitle">
      <div class="container section-head">
        <h2 id="newTitle">New arrivals</h2>
        <div class="scroller-nav">
          <a class="text-link" href="#/?all=1">View all</a>
          <button class="round-btn" data-scroll="-1" aria-label="Scroll left">‹</button>
          <button class="round-btn" data-scroll="1" aria-label="Scroll right">›</button>
        </div>
      </div>
      <div class="scroller" id="newInScroller" tabindex="0" aria-label="New arrivals, scroll sideways">
        ${items.map(renderProductCard).join('')}
      </div>
    </section>`;
}

function renderCampaigns(all) {
    const budget = all.filter(p => p.price <= 999);
    const kids = all.filter(p => p.category === 'kids' && p.image);
    const budgetImgs = budget.filter(p => p.image).slice(0, 2);
    const kidsImgs = kids.slice(2, 4);
    return `
    <section class="campaigns section" aria-label="Featured collections">
      ${budgetImgs.length ? `
      <a class="campaign campaign-dark" href="#/?max=999&all=1">
        <div class="campaign-imgs">${budgetImgs.map(p => `<img src="${escapeHtml(p.image)}" alt="" loading="lazy" />`).join('')}</div>
        <div class="campaign-copy">
          <p class="kicker">The everyday edit</p>
          <h2>All under ${formatPrice(999)}</h2>
          <p>${budget.length} easy pieces for every day — tees, tops and basics that don't stretch the budget.</p>
          <span class="btn btn-light">Shop the edit</span>
        </div>
      </a>` : ''}
      ${kidsImgs.length ? `
      <a class="campaign campaign-rose campaign-flip" href="#/?cat=kids">
        <div class="campaign-imgs">${kidsImgs.map(p => `<img src="${escapeHtml(p.image)}" alt="" loading="lazy" />`).join('')}</div>
        <div class="campaign-copy">
          <p class="kicker">Hem kids</p>
          <h2>Little ones, finished well</h2>
          <p>${all.filter(p => p.category === 'kids').length} play-ready and party-ready looks in soft fabrics they'll actually keep on.</p>
          <span class="btn btn-primary">Shop kids</span>
        </div>
      </a>` : ''}
    </section>`;
}

function renderEdit(all) {
    // dress-up pieces only (no pyjamas or tees), most premium first
    const picks = all.filter(p => matchesType(p, OCCASION.match)).sort((a, b) => b.price - a.price).slice(0, 8);
    if (!picks.length) return '';
    return `
    <section class="container section" aria-labelledby="editTitle">
      ${sectionHead('<span id="editTitle">The occasion edit</span>', { href: typeHref(OCCASION.match) + '&sort=price_desc', label: 'Shop the edit' })}
      <div class="grid" id="editGrid">${picks.map(renderProductCard).join('')}</div>
    </section>`;
}

function renderServices() {
    return `
    <section class="services" aria-label="Shopping with The House of Hem">
      <div class="container services-grid">
        <div><h3>Free delivery</h3><p>Across India, in 3–7 working days</p></div>
        <div><h3>7-day returns</h3><p>Unworn, with tags, no questions</p></div>
        <div><h3>Sizes XS to XL</h3><p>Plus one-size pieces</p></div>
        <div><h3>Private account</h3><p>Your bag and orders follow you</p></div>
      </div>
    </section>`;
}

/* ---------- listing ---------- */

function renderListingHeader(f, count) {
    const catLabel = f.category ? capitalize(f.category) : '';
    const typeName = f.type ? typeLabel(f.type, f.category) : '';
    const title = f.q
        ? `Results for “${escapeHtml(f.q)}”`
        : typeName && catLabel ? `${catLabel}'s ${typeName.toLowerCase()}`
        : typeName || catLabel || (f.max != null && f.min == null ? `Under ${formatPrice(f.max)}` : 'New in');
    return `
    <section class="listing-head">
      <div class="container">
        <nav class="crumbs" aria-label="Breadcrumb">
          <a href="#/">Home</a><span aria-hidden="true">/</span>
          ${catLabel && typeName ? `<a href="#/?cat=${f.category}">${catLabel}</a><span aria-hidden="true">/</span>` : ''}
          <span>${typeName || catLabel || (f.q ? 'Search' : 'New in')}</span>
        </nav>
        <h1>${title}</h1>
        <p>${count} ${count === 1 ? 'style' : 'styles'}</p>
      </div>
    </section>`;
}

function renderCatalog(f, products) {
    const types = f.category && MENU[f.category] ? MENU[f.category].types : null;
    return `
    <section class="catalog container" id="catalog" aria-labelledby="catalogTitle">
      <h2 id="catalogTitle" class="sr-only">Products</h2>
      ${types ? `
      <div class="type-chips" role="group" aria-label="Category">
        <a class="type-chip ${!f.type ? 'active' : ''}" href="${filterHash({ type: '' })}">All ${f.category}</a>
        ${types.map(t => `<a class="type-chip ${f.type === t.match ? 'active' : ''}" href="${filterHash({ type: t.match })}">${t.label}</a>`).join('')}
      </div>` : ''}
      <div class="toolbar">
        <div class="chips" role="group" aria-label="Price range">
          ${PRICE_RANGES.map(r => {
              const active = f.min === r.min && f.max === r.max;
              return `<button class="chip ${active ? 'active' : ''}" aria-pressed="${active}" data-min="${r.min ?? ''}" data-max="${r.max ?? ''}">${r.label}</button>`;
          }).join('')}
        </div>
        <label class="sort">
          <span>Sort by</span>
          <select id="sortSelect">
            ${SORTS.map(s => `<option value="${s.value}" ${f.sort === s.value ? 'selected' : ''}>${s.label}</option>`).join('')}
          </select>
        </label>
      </div>
      ${products.length === 0 ? `
        <div class="empty-state">
          <h3>Nothing matches yet</h3>
          <p>Try a different price range${f.q ? ' or a shorter search' : ''}, or see everything we stock.</p>
          <a class="btn btn-outline" href="#/?all=1">See all products</a>
        </div>` : `
        <div class="grid" id="productGrid">${products.slice(0, visible).map(renderProductCard).join('')}</div>
        ${renderMore(products.length)}`}
    </section>`;
}

function renderMore(total) {
    if (visible >= total) return '';
    const next = Math.min(PAGE_SIZE, total - visible);
    return `<div class="more"><p class="muted">Showing ${visible} of ${total}</p>
      <button class="btn btn-outline" id="showMoreBtn">Show ${next} more</button></div>`;
}

/* ---------- events ---------- */

function wireHomeEvents() {
    const app = document.getElementById('app');
    wireProductCards(app, lookup);

    app.querySelectorAll('.chip[data-min]:not([data-wired])').forEach(btn => {
        btn.dataset.wired = '1';
        btn.addEventListener('click', () => {
            const min = btn.dataset.min !== '' ? Number(btn.dataset.min) : null;
            const max = btn.dataset.max !== '' ? Number(btn.dataset.max) : null;
            navigate(filterHash({ min, max, all: true }));
        });
    });

    const sortSelect = document.getElementById('sortSelect');
    if (sortSelect && !sortSelect.dataset.wired) {
        sortSelect.dataset.wired = '1';
        sortSelect.addEventListener('change', (e) => navigate(filterHash({ sort: e.target.value, all: true })));
    }

    app.querySelectorAll('[data-scroll]:not([data-wired])').forEach(btn => {
        btn.dataset.wired = '1';
        btn.addEventListener('click', () => {
            const scroller = document.getElementById('newInScroller');
            scroller?.scrollBy({ left: Number(btn.dataset.scroll) * scroller.clientWidth * 0.8, behavior: 'smooth' });
        });
    });

    document.getElementById('showMoreBtn')?.addEventListener('click', () => {
        const grid = document.getElementById('productGrid');
        const start = visible;
        visible += PAGE_SIZE;
        grid.insertAdjacentHTML('beforeend', state.products.slice(start, visible).map(renderProductCard).join(''));
        document.querySelector('.more')?.remove();
        grid.insertAdjacentHTML('afterend', renderMore(state.products.length));
        wireHomeEvents();
        grid.children[start]?.querySelector('.card-title a')?.focus({ preventScroll: true });
    });
}
