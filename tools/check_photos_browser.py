"""Deterministic browser regression for available, missing, and failed product photos."""

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright, expect

from browser_fixtures import route_rows

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT)))
    Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}'
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            for mobile in (False, True):
                page = browser.new_page(viewport={'width': 390 if mobile else 1440, 'height': 900})
                rows = [{'id': state, 'title': state + ' photo test', 'price': 4000, 'url': base + '/product',
                         'image_url': image, 'series': 'Synthetic'} for state, image in
                        [('valid', '/test-photo.svg'), ('broken', '/photo404.png'), ('missing', '')]]
                route_rows(page, rows)
                page.route('**/test-photo.svg', lambda route: route.fulfill(content_type='image/svg+xml', body='<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><rect width="10" height="10" fill="blue"/></svg>'))
                page.route('**/photo404.png', lambda route: route.fulfill(status=404, body='Missing test photo'))
                page.goto(base + ('/mobile.html' if mobile else '/index.html'), wait_until='domcontentloaded')
                cards = page.locator('.m-card' if mobile else '.ticket')
                valid = cards.filter(has_text='valid photo test')
                expect(valid.locator('img')).to_have_attribute('src', base + '/test-photo.svg')
                expect(valid.locator('img')).to_be_visible()
                page.wait_for_function('Array.from(document.images).some(i => i.src.endsWith("/test-photo.svg") && i.naturalWidth === 10)')
                broken = cards.filter(has_text='broken photo test')
                expect(broken.locator('.photo-unavailable')).to_be_visible()
                expect(broken.locator('img')).to_be_hidden()
                missing = cards.filter(has_text='missing photo test')
                expect(missing.locator('img')).to_have_count(0)
                expect(missing.locator('.photo-unavailable')).to_be_visible()
                broken.locator('.m-detail-btn' if mobile else '.detail-btn').click()
                detail = page.locator('#mDetailBody' if mobile else '#detailModalBody')
                expect(detail.locator('.photo-unavailable')).to_be_visible()
                page.locator('#closeDetailSheet' if mobile else '#closeDetailModal').click()
                valid.locator('.m-detail-btn' if mobile else '.detail-btn').click()
                expect(detail.locator('img')).to_have_attribute('src', base + '/test-photo.svg')
                page.locator('#closeDetailSheet' if mobile else '#closeDetailModal').click()
                print(('Phone' if mobile else 'Desktop') + ': valid photo, failed-photo fallback, and missing-photo fallback passed')
                page.close()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    main()
