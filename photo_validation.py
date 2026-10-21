"""Bounded public image checks; never replace a photo with a guessed product."""

from copy import deepcopy
from datetime import datetime, timezone
import ipaddress
import time
from urllib.parse import urlsplit

import requests

from catalog_v2 import build_catalog
from source_photos import photo_url


def public_photo_url(value):
    url = photo_url(value, '')
    if not url:
        return None
    host = urlsplit(url).hostname
    if host == 'localhost' or '.' not in host:
        return None
    try:
        if not ipaddress.ip_address(host).is_global:
            return None
    except ValueError:
        pass
    return url


def image_signature(data, content_type):
    media = content_type.split(';')[0].strip().lower()
    return bool((media == 'image/jpeg' and data.startswith(b'\xff\xd8\xff')) or
                (media == 'image/png' and data.startswith(b'\x89PNG\r\n\x1a\n')) or
                (media == 'image/gif' and data.startswith((b'GIF87a', b'GIF89a'))) or
                (media == 'image/webp' and data.startswith(b'RIFF') and data[8:12] == b'WEBP') or
                (media == 'image/avif' and data[4:8] == b'ftyp' and b'avif' in data[8:40]) or
                (media == 'image/svg+xml' and b'<svg' in data.lower()))


class PhotoChecker:
    """Cache per run. At most 3 attempts, 3 redirects, and 512 body bytes per URL.

    HTTP reachability is distinct from a browser's successful image decode.
    Redirect destinations are checked before requesting them.
    """
    def __init__(self, session=None, *, sleep=time.sleep, clock=None):
        self.session = session or requests.Session()
        self.sleep = sleep
        self.clock = clock or (lambda: datetime.now(timezone.utc).isoformat())
        self.cache = {}

    def check(self, value):
        key = value if isinstance(value, str) else ''
        if key in self.cache:
            return deepcopy(self.cache[key])
        result = {'url': key or None, 'checked_at': self.clock(), 'state': 'missing' if not key else 'url_rejected',
                  'status': None, 'content_type': None, 'final_url': None}
        if public_photo_url(key):
            for attempt in range(3):
                current = key
                try:
                    for redirect in range(4):
                        if not public_photo_url(current):
                            result['state'] = 'url_rejected'
                            break
                        with self.session.get(current, stream=True, timeout=(5, 10), allow_redirects=False,
                                              headers={'Accept': 'image/*', 'User-Agent': 'LaptopPicker/1.0 photo check'}) as response:
                            status = response.status_code
                            result.update(status=status, content_type=response.headers.get('Content-Type', ''), final_url=current)
                            if status in (301, 302, 303, 307, 308):
                                location = response.headers.get('Location')
                                current = photo_url(location, current) if location else None
                                result['state'] = 'redirect_error'
                                if not current:
                                    break
                                continue
                            if status == 200:
                                prefix = next(response.iter_content(chunk_size=512), b'')
                                result['state'] = 'available' if image_signature(prefix, result['content_type']) else 'not_image'
                            else:
                                result['state'] = 'access_denied' if status in (401, 403) else 'http_error'
                            break
                    if result['status'] not in (429, 500, 502, 503, 504):
                        break
                except requests.RequestException:
                    result['state'] = 'network_error'
                if attempt < 2:
                    self.sleep(attempt + 1)
        self.cache[key] = deepcopy(result)
        return result


def validate_source_photos(results, previous=None, *, checker=None, generated_at=None):
    """Optional photo failures cannot reject an otherwise truthful priced offer.

    A previous photo may survive only for the same validated offer ID (which
    includes exact hardware) and after passing a new HTTP check. Evidence of its
    original extraction is preserved; the check time belongs to diagnostics.
    """
    checker = checker or PhotoChecker()
    results = deepcopy(results)
    previous_offers = {o['id']: o for o in previous['catalog']['offers']} if previous else {}
    audit = []
    for result in results:
        if result.mode != 'live' or result.status != 'complete':
            continue
        with_photos = build_catalog([result], generated_at=generated_at).catalog['offers']
        proven_photos = {o['id'] for o in with_photos if o.get('image_url')}
        identity_source = deepcopy(result)
        for record in identity_source.records:
            if isinstance(record.get('offer'), dict):
                record['offer'].pop('image_url', None)
                record['offer'].get('evidence', {}).pop('image_url', None)
        accepted = build_catalog([identity_source], generated_at=generated_at).catalog['offers']
        by_identity = {(o['source_product_id'], o['variant_id']): o for o in accepted}
        for record in result.records:
            offer = record.get('offer')
            if not offer:
                continue
            identity = (str(offer.get('source_product_id')), str(offer.get('variant_id')))
            validated = by_identity.get(identity)
            if validated is None:
                continue
            candidate = offer.get('image_url')
            check = checker.check(candidate) if not candidate or validated['id'] in proven_photos else {
                'url': None, 'state': 'unproven', 'checked_at': checker.clock(),
                'status': None, 'content_type': None, 'final_url': None}
            checks, retained = [check], False
            prior = previous_offers.get(validated['id'])
            if check['state'] != 'available' and prior and prior.get('image_url') and prior['image_url'] != candidate:
                prior_check = checker.check(prior['image_url'])
                checks.append(prior_check)
                if prior_check['state'] == 'available':
                    offer['image_url'] = prior['image_url']
                    offer['evidence']['image_url'] = deepcopy(prior['evidence']['image_url'])
                    retained = True
            if check['state'] != 'available' and not retained:
                offer.pop('image_url', None)
                offer['evidence'].pop('image_url', None)
            audit.append({'offer_id': validated['id'], 'source_id': result.source_id,
                          'state': 'available' if check['state'] == 'available' or retained else 'unavailable',
                          'retained_previous_photo': retained, 'checks': checks})
    return results, audit
