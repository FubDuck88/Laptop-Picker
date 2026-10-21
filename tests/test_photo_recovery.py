"""Photo recovery exercises the actual legacy parser paths with synthetic markup."""

import unittest
from pathlib import Path

from scrapers.techhypermart_scraper import extract_products_from_page
from scrapers import gloo_scraper


class PhotoRecoveryTests(unittest.TestCase):
    def test_captured_gloo_card_preserves_vendor_product_id_and_main_photo(self):
        html = (Path(__file__).parent / 'fixtures/captured/gloo_photo_card.html').read_text(encoding='utf-8')
        rows = gloo_scraper.extract_products_from_page(html)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['id'], '106421')
        self.assertEqual(rows[0]['image_url'], 'https://www.gloo.com.my/image/cache/catalog/Images/Notebook/NBKACERS7177TF_T1-500x500.jpg')

    def test_gloo_photo_comes_from_its_product_card_not_navigation(self):
        html = '''<a href="/laptop/gaming">Gaming Laptops</a>
        <div class="product-layout"><div class="product-image-container"><a href="/laptop-a" title="Acer Laptop A"><img src="/image/a.jpg"></a></div>
        <h4><a href="/laptop-a">Acer Laptop A</a></h4><span class="price">RM 3,999.00</span></div>'''
        rows = gloo_scraper.extract_products_from_page(html)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['image_url'], 'https://www.gloo.com.my/image/a.jpg')
        self.assertEqual(rows[0]['url'], 'https://www.gloo.com.my/laptop-a')

    def test_lazy_responsive_photo_is_one_real_url(self):
        html = '''<div class="product-layout"><a class="product-img" href="https://www.techhypermart.com/laptop-a">
        <img alt="Laptop A" src="data:image/gif;base64,AAAA" data-srcset="/image/a.jpg 420w, /image/a-large.jpg 840w"></a>
        <span class="price">RM 3999.00</span></div>'''
        rows, _ = extract_products_from_page(html)
        self.assertEqual(rows[0]['image_url'], 'https://www.techhypermart.com/image/a-large.jpg')


if __name__ == '__main__':
    unittest.main()
