"""Audit public photo reachability and optional real browser image decoding.

No saved prices are refreshed and deferred vendors are not qualified by this tool.
"""

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
from threading import Thread

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))

import requests

from photo_validation import PhotoChecker
from release_pipeline import atomic_write, encoded, load_release
from scrapers.gloo_scraper import extract_products_from_page as gloo_rows
from scrapers.pcimage_scraper import extract_products_from_html as pcimage_rows, BASE_URL as PCIMAGE
from scrapers.techhypermart_scraper import extract_products_from_page as tech_rows
from source_photos import photo_url


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def browser_checks(entries):
    from playwright.sync_api import sync_playwright
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT)))
    Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}'
    outcomes = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                for mobile in (False, True):
                    page = browser.new_page(viewport={'width': 390 if mobile else 1440, 'height': 900})
                    page.goto(base + '/index.html?desktop=1', wait_until='domcontentloaded')
                    page.evaluate('document.body.replaceChildren()')
                    for entry in entries:
                        row = {'title': entry['title'], 'image_url': entry['url'], 'url': entry['product_url']}
                        page.evaluate('([row, mobile]) => { document.body.innerHTML = renderProductImage(row, mobile); }', [row, mobile])
                        try:
                            page.wait_for_function('() => { const i=document.querySelector("[data-product-photo]"); return i && i.complete; }', timeout=15000)
                            decoded = page.locator('[data-product-photo]').evaluate('(i) => i.naturalWidth > 0 && i.naturalHeight > 0')
                            outcomes.append({'source_id': entry['source_id'], 'url': entry['url'], 'mobile': mobile,
                                             'state': 'displayed' if decoded else 'failed',
                                             'fallback_visible': page.locator('.photo-unavailable').is_visible()})
                        except Exception as error:
                            outcomes.append({'source_id': entry['source_id'], 'url': entry['url'], 'mobile': mobile,
                                             'state': 'timeout', 'error': type(error).__name__})
                    page.close()
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
    return outcomes


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=ROOT / 'data')
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/phase45-photos/audit.json')
    parser.add_argument('--refresh-vendors', action='store_true', help='Read one public listing page per affected deferred vendor')
    parser.add_argument('--browser', action='store_true', help='Verify actual external image decode in desktop and phone layouts')
    args = parser.parse_args(argv)
    checker = PhotoChecker()
    release = load_release(args.data_dir)
    if release is None:
        raise ValueError('A validated release is required')
    configs = {c['id']: c for c in release['catalog']['configurations']}
    entries = [{'source_id': o['source_id'], 'title': configs[o['configuration_id']]['title'],
                'product_url': o['url'], 'url': o.get('image_url')} for o in release['catalog']['offers']]
    pages = []
    if args.refresh_vendors:
        for source, url in [('gloo', 'https://www.gloo.com.my/laptops'), ('pcimage', PCIMAGE + '/collection/gaming-laptop'),
                            ('techhypermart', 'https://www.techhypermart.com/notebooks')]:
            detail = {'source_id': source, 'url': url, 'state': 'network_error'}
            try:
                with requests.get(url, timeout=(5, 20), stream=True, headers={'Accept': 'text/html', 'User-Agent': 'LaptopPicker/1.0 photo diagnostics'}) as response:
                    detail['status'] = response.status_code
                    detail['state'] = 'access_denied' if response.status_code in (401, 403) else 'page_unavailable'
                    if response.status_code == 200 and 'text/html' in response.headers.get('Content-Type', ''):
                        body = bytearray()
                        for chunk in response.iter_content(65536):
                            body.extend(chunk)
                            if len(body) > 2 * 1024 * 1024:
                                raise ValueError('Listing exceeds 2 MiB budget')
                        html = body.decode('utf-8', errors='replace')
                        rows = []
                        if source == 'gloo':
                            rows = gloo_rows(html)
                        elif source == 'techhypermart':
                            rows = tech_rows(html)[0]
                        else:
                            for item in pcimage_rows(html)[0][:24]:
                                product_url = PCIMAGE + '/product/' + (item.get('seo') or {}).get('url_handle', '')
                                image = next(iter(item.get('images') or []), {})
                                if not isinstance(image, dict):
                                    image = {}
                                rows.append({'title': item.get('name', ''), 'url': product_url,
                                             'image_url': photo_url(image.get('x420_url') or image.get('url'), product_url)})
                        detail.update(state='parsed' if rows else 'no_product_cards', products=len(rows))
                        entries.extend({'source_id': source, 'title': r['title'], 'product_url': r['url'], 'url': r.get('image_url')} for r in rows[:24])
            except (requests.RequestException, ValueError) as error:
                detail['error'] = type(error).__name__
            pages.append(detail)
    for entry in entries:
        entry['http'] = checker.check(entry['url'])
    browser = browser_checks([e for e in entries if e.get('url')]) if args.browser else []
    report = {'checked_at': checker.clock(), 'release_generated_at': release['generated_at'],
              'pages': pages, 'photos': entries, 'browser': browser}
    atomic_write(args.output, encoded(report))
    print(json.dumps({'photos': len(entries), 'http_available': sum(e['http']['state'] == 'available' for e in entries),
                      'browser_displayed': sum(r['state'] == 'displayed' for r in browser), 'browser_checks': len(browser),
                      'pages': pages, 'report': str(args.output)}, indent=2))
    return int(any(e['http']['state'] != 'available' for e in entries if e['source_id'] == 'allit') or
               any(r['state'] != 'displayed' for r in browser))


if __name__ == '__main__':
    raise SystemExit(main())
