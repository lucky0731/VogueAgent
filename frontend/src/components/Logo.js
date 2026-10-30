/**
 * The House of Hem lockup: small tracked "THE HOUSE OF" over a serif "HEM",
 * with a stitched rose hemline. `tone` is 'dark' (ink on light) or 'light'.
 */
export function logoSvg({ tone = 'dark', title = 'The House of Hem' } = {}) {
  const ink = tone === 'light' ? '#FAF7F4' : '#141213';
  const small = tone === 'light' ? '#CFC7C9' : '#6C6466';
  const stitch = tone === 'light' ? '#E7A9B8' : '#A9506A';
  return `<svg class="logo-svg" viewBox="0 0 240 100" role="img" aria-label="${title}">
    <text x="123" y="23" text-anchor="middle" font-family="Jost, sans-serif" font-weight="500" font-size="14.5" letter-spacing="6.5" fill="${small}">THE HOUSE OF</text>
    <text x="125" y="78" text-anchor="middle" font-family="Fraunces, Georgia, serif" font-weight="360" font-size="58" letter-spacing="10" fill="${ink}">HEM</text>
    <line x1="68" y1="92" x2="172" y2="92" stroke="${stitch}" stroke-width="2" stroke-dasharray="6 4.5"/>
  </svg>`;
}

/** Square "H" mark (favicon, small placements). */
export function markSvg() {
  return `<svg viewBox="0 0 96 96" aria-hidden="true"><rect width="96" height="96" rx="6" fill="#141213"/>
    <text x="48" y="62" text-anchor="middle" font-family="Fraunces, Georgia, serif" font-weight="380" font-size="44" fill="#FAF7F4">H</text>
    <line x1="18" y1="76" x2="78" y2="76" stroke="#E7A9B8" stroke-width="2.6" stroke-dasharray="6 4.5"/></svg>`;
}
