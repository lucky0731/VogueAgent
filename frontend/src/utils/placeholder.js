// Inline SVG used wherever a product has no image.
export const PLACEHOLDER_IMAGE =
    'data:image/svg+xml;utf8,' +
    encodeURIComponent(
        '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="500">' +
        '<rect width="100%" height="100%" fill="#F1ECE8"/>' +
        '<text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" ' +
        'fill="#6C6466" font-family="Georgia, serif" font-size="26" letter-spacing="6">HEM</text>' +
        '</svg>'
    );
