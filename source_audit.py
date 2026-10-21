"""Independent checks of fresh source associations against a validated release.

This does not certify manufacturer claims. Known normalized fields are paired with
their raw source evidence for review; the collector's normalizer is not rerun here.
"""

from decimal import Decimal, InvalidOperation
import json
from urllib.parse import parse_qs, urlsplit

from bs4 import BeautifulSoup


def structured_conditions(html):
    conditions = []

    def visit(value):
        if isinstance(value, list):
            for item in value:
                visit(item)
        elif isinstance(value, dict):
            types = value.get('@type')
            if types == 'Offer' or isinstance(types, list) and 'Offer' in types:
                conditions.append(value.get('itemCondition'))
            for item in value.values():
                if isinstance(item, (dict, list)):
                    visit(item)
    for script in BeautifulSoup(html, 'html.parser').select('script[type="application/ld+json"]'):
        try:
            visit(json.loads(script.get_text()))
        except (ValueError, TypeError):
            continue
    return bool(conditions) and all(c in ('https://schema.org/NewCondition', 'http://schema.org/NewCondition') for c in conditions)


def audit_allit_offer(offer, config, product, html):
    variants = [v for v in product.get('variants', []) if str(v.get('id')) == offer['variant_id']]
    variant = variants[0] if len(variants) == 1 else {}
    try:
        price = Decimal(str(variant.get('price'))) * 100
        price_matches = price.is_finite() and price == offer['price_sen']
    except (InvalidOperation, TypeError):
        price_matches = False
    available = variant.get('available')
    availability = 'in_stock' if available is True else 'out_of_stock' if available is False else 'unknown'
    body_text = BeautifulSoup(product.get('body_html') or '', 'html.parser').get_text(' ', strip=True)
    pool = ' '.join(str(v) for v in [product.get('title',''), variant.get('title',''), body_text,
                                     variant.get('option1',''),variant.get('option2',''),variant.get('option3','')])
    normalized = lambda s: ' '.join(str(s).replace('®','').replace('™','').split()).casefold()
    raw_fields = {}
    for field in ('cpu_model','gpu_model','gpu_kind','vram_gb','memory','storage','display'):
        proof = config['evidence'].get(field)
        if proof:
            fragments = proof['raw_value'].split(' / ')
            raw_fields[field] = {'normalized':config.get(field), 'raw':proof['raw_value'],
                                 'present_in_fresh_source':all(normalized(fragment) in normalized(pool) for fragment in fragments)}
    checks = {
        'seller': offer['seller'] == 'ALL IT' and offer['source_id'] == 'allit',
        'product_id': str(product.get('id')) == offer['source_product_id'],
        'variant_id': len(variants) == 1,
        'explicit_sku': bool(str(variant.get('sku') or '').strip()),
        'sku_evidence': config['evidence'].get('identity_scope',{}).get('raw_value','').endswith('SKU '+str(variant.get('sku'))),
        'part_number': normalized(config['manufacturer_part_number']) in normalized(product.get('title','')),
        'purchase_variant': parse_qs(urlsplit(offer['url']).query).get('variant') == [offer['variant_id']],
        'public_price': price_matches,
        'availability': availability == offer['availability'],
        'new_condition': structured_conditions(html),
        'known_field_evidence': all(v['present_in_fresh_source'] for v in raw_fields.values()),
    }
    return {'offer_id':offer['id'], 'manufacturer_part_number':config['manufacturer_part_number'],
            'variant_id':offer['variant_id'], 'sku':variant.get('sku'), 'price_sen':offer['price_sen'],
            'availability':offer['availability'], 'checks':checks, 'passed':all(checks.values()), 'fields':raw_fields}
