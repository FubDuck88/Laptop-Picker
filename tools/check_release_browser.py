"""Verify the real active release can be read and integrity-checked in Chromium."""

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
from threading import Thread

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from release_pipeline import load_release


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    expected = load_release(ROOT / 'data')
    if expected is None:
        raise ValueError('Collect a verified release before running this check')
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT)))
    Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}'
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(base + '/index.html', wait_until='domcontentloaded')
            page.add_script_tag(url=base + '/js/release.js')
            actual = page.evaluate('async () => { const r = await loadVerifiedRelease(); return {generated_at:r.generated_at, offers:r.catalog.offers.length}; }')
            assert actual['generated_at'] == expected['generated_at']
            assert actual['offers'] == len(expected['catalog']['offers'])
            page.route('**/data/releases/*.json', lambda route: route.fulfill(content_type='application/json', body='{}'))
            error = page.evaluate('async () => { try { await loadVerifiedRelease(); return null; } catch(e) { return e.message; } }')
            assert error == 'Catalog integrity check failed', error
            print(f"Chromium verified-release reader: {actual['offers']} offers loaded; corrupted data rejected")
            browser.close()
    finally:
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    main()
