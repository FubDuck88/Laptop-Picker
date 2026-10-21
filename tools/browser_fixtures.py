"""Synthetic verified releases for UI checks, delivered through real hashed endpoints.

The fixture's explicit default display is test data, never a retailer observation.
There is no test-data bypass in the application loader.
"""
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from catalog_v2 import SourceResult
from release_pipeline import build_release, encoded
from source_normalization import capacity
from source_photos import photo_url


def fixture_release(rows, *, as_of=None, previous=None):
    current = as_of or datetime.now(timezone.utc)
    observed = (current - timedelta(minutes=2)).isoformat()
    grouped = defaultdict(list)
    for index, row in enumerate(rows):
        for seller_index in range(row.get('vendor_count', 1)):
            seller = row.get('series') or 'Synthetic store'
            if row.get('vendor_count', 1) > 1:
                seller = f'Seller {seller_index + 1}'
            url = row.get('url') or 'https://example.com/laptop'
            proof = lambda raw: {'source_url': url, 'observed_at': observed, 'method': 'structured', 'raw_value': str(raw)}
            config = {'brand': 'Synthetic', 'manufacturer_part_number': f'TEST-{index}',
                      'title': row['title'], 'product_type': 'laptop', 'identity_scope': 'exact_variant',
                      'evidence': {key: proof(raw) for key, raw in {'brand':'Synthetic', 'manufacturer_part_number': f'TEST-{index}',
                                   'product_type':'laptop', 'identity_scope':'Explicit synthetic configuration'}.items()}}
            for field, raw in [('cpu_model',row.get('processor')), ('gpu_model',row.get('graphics'))]:
                if raw:
                    config[field] = raw
                    config['evidence'][field] = proof(raw)
            if row.get('graphics'):
                import re
                config['gpu_kind'] = 'integrated' if 'integrated' in row['graphics'].lower() or 'Arc Graphics' in row['graphics'] else 'discrete'
                config['evidence']['gpu_kind'] = proof(config['gpu_kind'])
                match = re.search(r'(\d+)GB\s*GDDR', row['graphics'], re.I)
                if match:
                    config['vram_gb'] = int(match[1])
                    config['evidence']['vram_gb'] = proof(match[0])
            for field in ('memory','storage'):
                parsed = capacity(row.get(field, ''), field)
                if parsed:
                    config[field] = parsed
                    config['evidence'][field] = proof(row[field])
            config['display'] = {'diagonal_inches':15.6, 'resolution_width':1920, 'resolution_height':1080, 'refresh_hz':144, 'label':'15.6 inch 1920x1080 144Hz'}
            config['evidence']['display'] = proof('Explicit synthetic display 15.6 inch 1920x1080 144Hz')
            offer = {'source_product_id':row.get('id',str(index)), 'variant_id':'fixture-variant', 'seller':seller,
                     'url':url, 'price_myr':str(Decimal(str(row.get('price',4000))) + seller_index * 100),
                     'currency':'MYR', 'price_basis':'public', 'condition':'new', 'availability':row.get('availability','unknown'),
                     'observed_at':observed, 'evidence':{}}
            for key in ('source_product_id','variant_id','seller','url','price','price_basis','condition','availability'):
                offer['evidence'][key] = proof(offer['price_myr'] if key == 'price' else offer[key])
            image = photo_url(row.get('image_url'),url)
            if image:
                offer['image_url'] = image
                offer['evidence']['image_url'] = proof(image)
            grouped[seller].append({'configuration':config,'offer':offer})
    results = [SourceResult(f'fixture_{i}', 'complete', records=records,
                           started_at=(current-timedelta(minutes=3)).isoformat(),
                           finished_at=(current-timedelta(minutes=1)).isoformat()) for i,records in enumerate(grouped.values())]
    release, diagnostics = build_release(results, previous, generated_at=current.isoformat())
    if len(release['catalog']['offers']) != sum(row.get('vendor_count',1) for row in rows):
        raise AssertionError(f'Invalid synthetic UI fixture: {diagnostics}')
    return release


def route_release(page, release):
    payload = encoded(release)
    checksum = hashlib.sha256(payload).hexdigest()
    pointer = {'release_version':1, 'path':f'releases/{checksum}.json','sha256':checksum}
    page.route('**/data/current.json', lambda route: route.fulfill(content_type='application/json', body=encoded(pointer)))
    page.route('**/data/releases/*.json', lambda route: route.fulfill(content_type='application/json', body=payload))


def route_rows(page, rows):
    route_release(page, fixture_release(rows))
