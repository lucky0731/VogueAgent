import { state } from '../services/state.js';
import { navigate, currentRoute } from '../services/nav.js';
import { wishlistCount } from '../services/wishlist.js';
import { escapeHtml } from '../utils/escapeHtml.js';
import { MENU, typeHref } from '../utils/catalogTypes.js';
import { PLACEHOLDER_IMAGE } from '../utils/placeholder.js';
import { logoSvg } from './Logo.js';

const ICON_USER = '<svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>';
const ICON_BAG = '<svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M6 7h12l1 14H5L6 7z"/><path d="M9 7a3 3 0 0 1 6 0"/></svg>';
const ICON_HEART = '<svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"><path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/></svg>';
const ICON_SEARCH = '<svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>';
const ICON_MENU = '<svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"><path d="M3 7h18M3 12h18M3 17h18"/></svg>';

let searchOpen = false;

/** Close the search bar (called by the router when the page changes). */
export function resetHeaderSearch() {
  searchOpen = false;
}

function featured(cat) {
  return (state.allProducts || []).filter(p => p.category === cat && p.image).slice(1, 3);
}

function renderMega(cat) {
  const menu = MENU[cat];
  const picks = featured(cat);
  return `
  <div class="mega" role="region" aria-label="${menu.label} menu">
    <div class="container mega-inner">
      <div class="mega-col">
        <p class="mega-title">Shop ${menu.label.toLowerCase()}</p>
        <a href="#/?cat=${cat}">View all</a>
        <a href="#/?cat=${cat}&sort=newest&all=1">New in</a>
        <a href="#/?cat=${cat}&max=999">Under ₹999</a>
      </div>
      <div class="mega-col mega-types">
        <p class="mega-title">Categories</p>
        ${menu.types.map(t => `<a href="${typeHref(t.match, cat)}">${t.label}</a>`).join('')}
      </div>
      <div class="mega-feature">
        ${picks.map(p => `
          <a class="mega-card" href="#/product/${escapeHtml(p.id)}">
            <img src="${escapeHtml(p.image || PLACEHOLDER_IMAGE)}" alt="" loading="lazy" />
            <span>${escapeHtml(p.name)}</span>
          </a>`).join('')}
      </div>
    </div>
  </div>`;
}

export function renderHeader() {
  const { path } = currentRoute();
  const onCatalog = path === '/';
  const { category, q } = state.filters;
  if (onCatalog && q) searchOpen = true;
  const wish = wishlistCount();
  return `
  <div class="announce">Free delivery across India<span class="announce-more"> · Easy 7-day returns · Sizes XS to XL</span></div>
  <header class="header ${searchOpen ? 'search-open' : ''}">
    <div class="container header-inner">
      <div class="header-left">
        <button class="menu-btn" id="menuToggle" aria-label="Open menu" aria-expanded="false">${ICON_MENU}</button>
        <nav class="nav" id="mainNav" aria-label="Main">
          ${Object.entries(MENU).map(([cat, m]) => `
            <div class="nav-item">
              <button class="nav-link ${onCatalog && category === cat ? 'active' : ''}" data-cat="${cat}" aria-haspopup="true">${m.label}</button>
              ${renderMega(cat)}
              <div class="drawer-types">
                ${m.types.map(t => `<a href="${typeHref(t.match, cat)}">${t.label}</a>`).join('')}
              </div>
            </div>`).join('')}
          <div class="nav-item"><button class="nav-link" data-cat="">New in</button></div>
        </nav>
      </div>
      <a class="logo" href="#/" aria-label="The House of Hem, home">${logoSvg()}</a>
      <div class="header-actions">
        <button class="icon-btn" id="searchToggle" aria-label="Search" aria-expanded="${searchOpen}">${ICON_SEARCH}</button>
        ${state.isAdmin ? `<a class="admin-link" href="#/admin">Manage store</a>` : ''}
        <a class="icon-btn" href="#/profile" aria-label="${state.isLoggedIn ? `Your account, ${escapeHtml(state.username)}` : 'Log in'}">
          ${ICON_USER}<span class="icon-label">${state.isLoggedIn ? escapeHtml(state.username) : 'Log in'}</span>
        </a>
        <a class="icon-btn wish-link" href="#/wishlist" aria-label="Wishlist, ${wish} items">
          ${ICON_HEART}${wish > 0 ? `<span class="badge">${wish}</span>` : ''}
        </a>
        <a class="icon-btn bag-link" href="#/cart" aria-label="Bag, ${state.cartItemCount} items">
          ${ICON_BAG}${state.cartItemCount > 0 ? `<span class="badge">${state.cartItemCount}</span>` : ''}
        </a>
      </div>
    </div>
    <div class="search-panel">
      <form class="container search" id="headerSearch" role="search">
        <label class="sr-only" for="searchInput">Search products</label>
        ${ICON_SEARCH}
        <input id="searchInput" type="search" placeholder="Search dresses, shirts, jeans, jackets…" value="${escapeHtml(onCatalog ? q : '')}" autocomplete="off" />
        <button type="submit" class="search-go">Search</button>
      </form>
    </div>
  </header>`;
}

export function mountHeader() {
  const host = document.getElementById('site-header');
  if (!host) return;
  host.innerHTML = renderHeader();
  const header = host.querySelector('.header');
  const closeMenus = () => {
    header.classList.remove('nav-open');
    host.querySelectorAll('.nav-item.open').forEach(i => i.classList.remove('open'));
    document.activeElement?.blur?.();
  };

  host.querySelectorAll('.nav-link[data-cat]').forEach(el => {
    el.addEventListener('click', () => {
      // On the mobile drawer, the first tap on a category expands its types.
      const item = el.closest('.nav-item');
      if (header.classList.contains('nav-open') && item.querySelector('.drawer-types') && !item.classList.contains('open')) {
        host.querySelectorAll('.nav-item.open').forEach(i => i.classList.remove('open'));
        item.classList.add('open');
        return;
      }
      navigate(el.dataset.cat ? `#/?cat=${el.dataset.cat}` : '#/?all=1');
      closeMenus();
    });
  });
  host.querySelectorAll('.mega a, .drawer-types a').forEach(a => a.addEventListener('click', closeMenus));

  host.querySelector('#searchToggle')?.addEventListener('click', () => {
    searchOpen = !header.classList.contains('search-open');
    header.classList.toggle('search-open', searchOpen);
    host.querySelector('#searchToggle').setAttribute('aria-expanded', String(searchOpen));
    if (searchOpen) host.querySelector('#searchInput')?.focus();
  });

  host.querySelector('#headerSearch')?.addEventListener('submit', (e) => {
    e.preventDefault();
    const q = host.querySelector('#searchInput').value.trim();
    navigate(q ? `#/?q=${encodeURIComponent(q)}` : '#/?all=1');
  });

  const toggle = host.querySelector('#menuToggle');
  toggle?.addEventListener('click', () => {
    const open = header.classList.toggle('nav-open');
    toggle.setAttribute('aria-expanded', String(open));
  });
}
