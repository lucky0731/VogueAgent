import { escapeHtml } from '../utils/escapeHtml.js';
import { PLACEHOLDER_IMAGE } from '../utils/placeholder.js';

/**
 * Full-bleed campaign hero: three edge-to-edge photos (women, men, kids), each
 * a link into its category, with the headline over the middle.
 */
export function renderHero(products) {
  const panels = ['women', 'men', 'kids'].map(cat => {
    const imgs = products.filter(p => p.category === cat && p.image);
    return { cat, product: imgs[0] };
  });
  return `
  <section class="hero" aria-label="New season">
    <div class="hero-panels">
      ${panels.map(({ cat, product }) => `
        <a class="hero-panel" href="#/?cat=${cat}">
          <img src="${escapeHtml(product?.image || PLACEHOLDER_IMAGE)}" alt="" />
          <span class="hero-panel-label">Shop ${cat}</span>
        </a>`).join('')}
    </div>
    <div class="hero-copy">
      <p class="hero-kicker">The new season</p>
      <h1 class="hero-title">Finished to the last stitch</h1>
      <div class="hero-actions">
        <a class="btn btn-light" href="#/?cat=women">Shop women</a>
        <a class="btn btn-light-outline" href="#/?cat=men">Shop men</a>
      </div>
    </div>
  </section>`;
}
