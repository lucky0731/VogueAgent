import { logoSvg } from './Logo.js';
import { POPULAR, typeHref } from '../utils/catalogTypes.js';

const YEAR = new Date().getFullYear();

export function mountFooter() {
  const host = document.getElementById('site-footer');
  if (!host) return;
  host.innerHTML = `
  <footer class="footer">
    <div class="container footer-grid">
      <div class="footer-brand">
        <a href="#/" class="footer-logo" aria-label="The House of Hem, home">${logoSvg({ tone: 'light' })}</a>
        <p>Clothing for women, men and kids, finished with care down to the last stitch.</p>
      </div>
      <nav aria-label="Shop">
        <h2>Shop</h2>
        <a href="#/?cat=women">Women</a>
        <a href="#/?cat=men">Men</a>
        <a href="#/?cat=kids">Kids</a>
        <a href="#/?all=1">New in</a>
        <a href="#/?max=999&all=1">Under ₹999</a>
      </nav>
      <div>
        <h2>Help</h2>
        <p>Free delivery across India in 3–7 working days.</p>
        <p>Returns within 7 days of delivery, unworn with tags.</p>
        <p>Sizes from XS to XL on most styles.</p>
      </div>
      <nav aria-label="Your account">
        <h2>Your account</h2>
        <a href="#/profile">Profile and orders</a>
        <a href="#/wishlist">Wishlist</a>
        <a href="#/cart">Bag</a>
      </nav>
    </div>
    <div class="container footer-popular">
      <h2>Most searched</h2>
      <p>${POPULAR.map(p => `<a href="${typeHref(p.match, p.cat || '')}">${p.label}</a>`).join('<span aria-hidden="true">|</span>')}</p>
    </div>
    <div class="container footer-base">
      <p>© ${YEAR} The House of Hem. All rights reserved.</p>
    </div>
  </footer>`;
}
