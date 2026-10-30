/**
 * Product types used by the menus, category tiles and listing chips.
 * `match` is passed to GET /products?type=... (matched against the end of the
 * product name, e.g. "Slim Fit Blue Jeans" → Jeans).
 */
export const MENU = {
    women: {
        label: 'Women',
        types: [
            { label: 'Dresses', match: 'Dress' },
            { label: 'Skirts', match: 'Skirt' },
            { label: 'Tops & blouses', match: 'Blouse,T-Shirt' },
            { label: 'Jackets & coats', match: 'Jacket,Coat' },
            { label: 'Knitwear', match: 'Sweater,Cardigan' },
            { label: 'Denim', match: 'Jeans' },
            { label: 'Kurtis', match: 'Kurti' },
        ],
    },
    men: {
        label: 'Men',
        types: [
            { label: 'Shirts', match: 'Shirt' },
            { label: 'T-shirts', match: 'T-Shirt,Tee' },
            { label: 'Knitwear', match: 'Sweater' },
            { label: 'Hoodies', match: 'Hoodie' },
            { label: 'Jackets', match: 'Jacket' },
            { label: 'Suits', match: 'Suit' },
            { label: 'Jeans', match: 'Jeans' },
            { label: 'Chinos & shorts', match: 'Chinos,Shorts' },
        ],
    },
    kids: {
        label: 'Kids',
        types: [
            { label: 'Dresses', match: 'Dress' },
            { label: 'T-shirts', match: 'T-Shirt' },
            { label: 'Sweaters & hoodies', match: 'Sweater,Hoodie' },
            { label: 'Jackets', match: 'Jacket' },
            { label: 'Pyjamas', match: 'Pajamas' },
            { label: 'Shorts & jeans', match: 'Shorts,Jeans,Dungaree' },
        ],
    },
};

/** Cross-category tiles for the home page "Shop by category" row. */
export const HOME_TYPES = [
    { label: 'Dresses', match: 'Dress' },
    { label: 'Shirts', match: 'Shirt' },
    { label: 'Jackets', match: 'Jacket,Coat' },
    { label: 'Knitwear', match: 'Sweater,Cardigan' },
    { label: 'Denim', match: 'Jeans' },
    { label: 'T-shirts', match: 'T-Shirt,Tee' },
];

/** Curated edits used on the home page. */
export const OCCASION = { label: 'Occasion wear', match: 'Dress,Suit,Jacket,Coat,Skirt,Blouse,Cardigan' };

/** "Most searched" links in the footer. */
export const POPULAR = [
    { label: 'Dresses', match: 'Dress' }, { label: 'Jeans', match: 'Jeans' },
    { label: 'Jackets', match: 'Jacket' }, { label: 'Sweaters', match: 'Sweater' },
    { label: 'Skirts', match: 'Skirt' }, { label: 'Shirts', match: 'Shirt' },
    { label: 'Hoodies', match: 'Hoodie' }, { label: 'Suits', match: 'Suit' },
    { label: 'Cardigans', match: 'Cardigan' }, { label: 'Kids pyjamas', match: 'Pajamas', cat: 'kids' },
];

/** Does a product's name end in one of the comma-separated types? (mirrors the backend rule) */
export function matchesType(product, match) {
    const types = match.split(',').map(t => t.trim().toLowerCase());
    const name = String(product.name || '').toLowerCase();
    return types.some(t => name === t || name.endsWith(' ' + t));
}

export function typeHref(match, cat = '') {
    const params = new URLSearchParams();
    if (cat) params.set('cat', cat);
    params.set('type', match);
    return `#/?${params}`;
}

/** Human label for a type value in the current category, for titles and chips. */
export function typeLabel(match, cat = '') {
    const pools = cat && MENU[cat] ? [MENU[cat].types] : [...Object.values(MENU).map(m => m.types), HOME_TYPES, [OCCASION]];
    for (const pool of pools) {
        const hit = pool.find(t => t.match === match);
        if (hit) return hit.label;
    }
    return match.split(',')[0];
}
