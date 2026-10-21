"""Photo provenance regressions; input URLs are synthetic, not retailer captures."""

import json
from pathlib import Path
import unittest

from source_adapters import allit_records
from source_photos import photo_url, shopify_photo
from catalog_v2 import build_catalog
from test_catalog_v2 import record, source, GENERATED


class PhotoExtractionTests(unittest.TestCase):
    def test_variant_photo_is_preserved_in_the_native_offer(self):
        item = json.loads((Path(__file__).parent / 'fixtures/regressions.json').read_text(encoding='utf-8'))['shopify_variants']
        item.update(title='HP Laptop 15-FA2547TX', product_type='NOTEB', options=[{'name': 'Memory'}])
        item['variants'][0].update(option1='16GB', image_id=2)
        item['variants'][1].update(option1='32GB', image_id=3)
        item['images'] = [{'id': 1, 'src': 'https://cdn.shopify.com/product.jpg'}, {'id': 2, 'src': '//cdn.shopify.com/variant16.jpg'}, {'id': 3, 'src': 'https://cdn.shopify.com/variant32.jpg'}]
        rows = allit_records(item, '2026-10-20T00:15:00Z')
        self.assertEqual(rows[0]['offer'].get('image_url'), 'https://cdn.shopify.com/variant16.jpg')
        self.assertEqual(rows[1]['offer'].get('image_url'), 'https://cdn.shopify.com/variant32.jpg')

    def test_missing_variant_image_never_borrows_another_variants_photo(self):
        product = {'images': [{'id': 2, 'src': '/blue.jpg', 'variant_ids': [2]}]}
        self.assertIsNone(shopify_photo(product, {'id': 1, 'image_id': 1}, 'https://shop.example/item'))
        self.assertIsNone(shopify_photo(product, {'id': 1}, 'https://shop.example/item'))
        self.assertEqual(shopify_photo(product, {'id': 2}, 'https://shop.example/item'), 'https://shop.example/blue.jpg')

    def test_relative_urls_preserve_query_and_reject_unsafe_values(self):
        self.assertEqual(photo_url('/img/item.jpg?v=2', 'https://shop.example/products/item'), 'https://shop.example/img/item.jpg?v=2')
        for value in ('javascript:alert(1)', 'data:image/png;base64,xyz', 'https://user:password@shop.example/image.jpg', 'not a URL'):
            self.assertIsNone(photo_url(value, 'https://shop.example/products/item'))

    def test_image_metadata_needs_provenance_and_does_not_change_offer_identity(self):
        item = record()
        before = build_catalog([source([item])], generated_at=GENERATED)
        item['offer']['image_url'] = 'https://cdn.example/actual.jpg'
        missing = build_catalog([source([item])], generated_at=GENERATED)
        self.assertEqual(missing.catalog['offers'], [])
        item['offer']['evidence']['image_url'] = dict(item['offer']['evidence']['url'], raw_value=item['offer']['image_url'])
        after = build_catalog([source([item])], generated_at=GENERATED)
        self.assertEqual(after.catalog['offers'][0]['id'], before.catalog['offers'][0]['id'])
        self.assertEqual(after.catalog['offers'][0]['image_url'], item['offer']['image_url'])
        item['offer']['evidence']['image_url']['raw_value'] = 'https://cdn.example/different.jpg'
        self.assertEqual(build_catalog([source([item])], generated_at=GENERATED).catalog['offers'], [])


if __name__ == '__main__':
    unittest.main()
