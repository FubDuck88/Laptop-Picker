"""Preserve actual source photos without guessing another laptop's image."""

from urllib.parse import urljoin, urlsplit
import re


def element_photo(element, product_url):
    """Select one URL, preferring real lazy images over placeholder src values.

    Callers must pass the image from the exact product card, never the page.
    Responsive candidates with unsupported/mixed descriptors are ignored.
    """
    if element is None:
        return None
    for field in ('data-src', 'data-original', 'data-lazy-src', 'data-srcset', 'srcset', 'src'):
        value = element.get(field)
        if not isinstance(value, str):
            continue
        if field.endswith('srcset'):
            candidates = []
            for part in value.split(','):
                match = re.fullmatch(r'\s*(\S+)\s+(\d+(?:\.\d+)?)(w|x)\s*', part)
                if match and float(match[2]) > 0:
                    url = photo_url(match[1], product_url)
                    if url:
                        candidates.append((float(match[2]), match[3], url))
            if candidates and len({c[1] for c in candidates}) == 1:
                return max(candidates, key=lambda c: c[0])[2]
        else:
            url = photo_url(value, product_url)
            if url:
                return url
    return None


def photo_url(value, product_url):
    if not isinstance(value, str) or not value.strip():
        return None
    value = value.strip()
    if any(c.isspace() for c in value) or value.startswith(('data:', 'javascript:')):
        return None
    if value.startswith('//'):
        value = 'https:' + value
    else:
        value = urljoin(product_url, value)
    try:
        parsed = urlsplit(value)
        if parsed.scheme not in {'http', 'https'} or not parsed.hostname or parsed.username or parsed.password or parsed.port == 0:
            return None
    except ValueError:
        return None
    return value


def shopify_photo(product, variant, product_url):
    featured = variant.get('featured_image')
    if isinstance(featured, dict) and featured.get('src'):
        return photo_url(featured['src'], product_url)
    images = [image for image in product.get('images', []) if isinstance(image, dict)]
    if variant.get('image_id'):
        image = next((image for image in images if str(image.get('id')) == str(variant['image_id'])), None)
        return photo_url(image.get('src'), product_url) if image else None
    scoped = [image for image in images if str(variant.get('id')) in {str(v) for v in image.get('variant_ids', [])}]
    generic = [image for image in images if not image.get('variant_ids')]
    selected = next(iter(scoped or generic), None)
    return photo_url(selected.get('src'), product_url) if selected else None
