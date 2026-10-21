"""Optional real Chromium checks. Serves localhost only; never changes catalog data."""

import argparse
from datetime import datetime, timedelta, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
from threading import Thread

from playwright.sync_api import sync_playwright, expect

from browser_fixtures import fixture_release, route_release, route_rows
from release_pipeline import load_release

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def copyfile(self, source, outputfile):
        try:
            super().copyfile(source, outputfile)
        except (ConnectionAbortedError, BrokenPipeError):
            pass  # Phone redirects can cancel an in-flight local asset.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args()
    output = args.output_dir or Path(tempfile.mkdtemp(prefix='laptop-picker-browser-'))
    output.mkdir(parents=True, exist_ok=True)
    report = {'observed_at': datetime.now(timezone.utc).isoformat(), 'checks': [], 'pages': []}

    def check(name, action):
        try:
            action()
            report['checks'].append({'name': name, 'status': 'pass'})
        except Exception as error:
            report['checks'].append({'name': name, 'status': 'fail', 'error': str(error)[:1600]})

    def require(condition, message):
        if not condition:
            raise AssertionError(message)

    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT)))
    Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}'
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            report['chromium_version'] = browser.version

            def page_for(name, mobile=False, fixture=None):
                options = {'viewport': {'width': 390 if mobile else 1440, 'height': 844 if mobile else 900}}
                if mobile:
                    options.update(is_mobile=True, has_touch=True, device_scale_factor=1,
                                   user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148')
                context = browser.new_context(**options)
                context.set_default_timeout(7000)
                page = context.new_page()
                details = {'name': name, 'errors': [], 'failed_requests': [], 'bad_responses': []}
                report['pages'].append(details)
                page.on('pageerror', lambda error: details['errors'].append(str(error)))
                page.on('requestfailed', lambda request: details['failed_requests'].append({'url': request.url, 'reason': request.failure}))
                page.on('response', lambda response: details['bad_responses'].append({'url': response.url, 'status': response.status}) if response.status >= 400 else None)
                if fixture is not None:
                    route_rows(page, fixture)
                return page, details

            def overflow(page):
                values = page.evaluate('({viewport:document.documentElement.clientWidth, content:document.documentElement.scrollWidth})')
                require(values['content'] <= values['viewport'] + 1, str(values))

            def snapshot(page, name):
                page.wait_for_function('() => Array.from(document.images).filter(i => i.hasAttribute("data-product-photo") && i.getBoundingClientRect().top < innerHeight).every(i => i.complete)', timeout=10000)
                check(name + ': screenshot', lambda: page.screenshot(path=str(output / (name + '.png')), timeout=10000))

            desktop, desktop_details = page_for('desktop')
            desktop.goto(base + '/index.html', wait_until='domcontentloaded')
            check('desktop: catalog loads', lambda: expect(desktop.locator('#grid .ticket').first).to_be_visible())
            def prices_sorted(page, selector):
                prices = page.locator(selector).all_inner_texts()
                import re
                numbers = [float(re.sub(r"[^0-9.]", "", text)) for text in prices if re.search(r"\d", text)]
                require(len(numbers) > 1 and numbers == sorted(numbers), str(numbers))

            check('desktop: price ascending sort', lambda: (desktop.locator('#sortSelect').select_option('price-asc'), prices_sorted(desktop, '#grid .price-tag')))
            desktop.locator('#sortSelect').select_option('recommended')
            initial_count = desktop.locator('#resultCount').inner_text()
            report['desktop_initial_count'] = initial_count
            snapshot(desktop, 'desktop')
            check('desktop: no horizontal overflow', lambda: overflow(desktop))
            check('desktop: small catalog needs no pagination', lambda: expect(desktop.locator('#loadMoreBtn')).to_have_count(0))
            check('desktop: empty search', lambda: (desktop.locator('#searchInput').fill('zzzz-no-such-laptop-zzzz'), expect(desktop.locator('#grid .ticket')).to_have_count(0)))
            check('desktop: reset restores catalog', lambda: (desktop.locator('#resetBtn').click(), expect(desktop.locator('#resultCount')).to_have_text(initial_count)))
            check('desktop: price filter', lambda: (desktop.locator('#maxPrice').fill('3000'), require(desktop.locator('#grid .ticket').count() > 0, 'No results'), require(desktop.evaluate('getFiltered().every(r=>r.price<=3000)'), 'Price ceiling violated')))
            desktop.locator('#resetBtn').click()
            check('desktop: specs modal', lambda: (desktop.locator('.detail-btn').first.click(), expect(desktop.locator('#detailModalOverlay')).to_have_class('modal-overlay show'), desktop.locator('#closeDetailModal').click()))
            check('desktop: comparison', lambda: (desktop.locator('.compare-check').nth(0).click(), desktop.locator('.compare-check').nth(1).click(), desktop.locator('#openCompare').click(), expect(desktop.locator('#compareTableWrap table')).to_be_visible(), desktop.locator('#closeModal').click()))

            mobile, mobile_details = page_for('mobile', mobile=True)
            mobile.goto(base + '/index.html', wait_until='domcontentloaded')
            check('phone: automatic mobile redirect', lambda: expect(mobile).to_have_url(base + '/mobile.html'))
            check('phone: catalog loads', lambda: expect(mobile.locator('#mGrid .m-card').first).to_be_visible())
            check('phone: price ascending sort', lambda: (mobile.locator('#mSortSelect').select_option('price-asc'), prices_sorted(mobile, '.m-price-tag')))
            mobile.locator('#mSortSelect').select_option('recommended')
            snapshot(mobile, 'phone')
            check('phone: no horizontal overflow', lambda: overflow(mobile))
            check('phone: search and reset', lambda: (mobile.locator('#mSearchInput').fill('zzzz-no-such-laptop-zzzz'), expect(mobile.locator('#mGrid .m-card')).to_have_count(0), mobile.locator('#chipAll').click(), expect(mobile.locator('#mGrid .m-card').first).to_be_visible()))
            check('phone: filter sheet', lambda: (mobile.locator('#navFilterSheet').click(), expect(mobile.locator('#mFilterOverlay')).to_have_class('m-sheet-overlay show'), mobile.locator('[data-target="mfg-price"]').click(), mobile.locator('#mMaxPrice').fill('3000'), mobile.locator('#applyMobileFilterBtn').click(), require(mobile.evaluate('getMobileFiltered().every(r=>r.price<=3000)'), 'Price ceiling violated')))
            mobile.reload(wait_until='domcontentloaded')
            expect(mobile.locator('#mGrid .m-card').first).to_be_visible()
            mobile.locator('#chipAll').click()
            check('phone: specs sheet', lambda: (mobile.locator('.m-detail-btn').first.click(), expect(mobile.locator('#mDetailOverlay')).to_have_class('m-sheet-overlay show'), mobile.locator('#closeDetailSheet').click()))
            check('phone: desktop switch', lambda: (mobile.get_by_role('link', name='Desktop').click(), expect(mobile).to_have_url(base + '/index.html?desktop=1')))

            analytics, analytics_details = page_for('analytics')
            analytics.goto(base + '/analytics.html', wait_until='domcontentloaded')
            check('analytics: populated directory', lambda: expect(analytics.locator('#analyticsTableBody tr').first).to_be_visible())
            def honest_history():
                selected = analytics.locator('#historyOffer').input_value()
                active = load_release(ROOT / 'data')
                points = {r['observation']['observed_at'] for r in active['history']['receipts'] if r['observation']['offer_id'] == selected}
                text = 'One observation; no price trend yet.' if len(points) == 1 else f'{len(points)} recorded observations for this exact seller offer.'
                expect(analytics.locator('#priceHistoryUnavailable')).to_have_text(text)
                expect(analytics.locator('#priceHistoryBody tbody tr')).to_have_count(len(points))
            check('analytics: honest history state', honest_history)
            check('analytics: price statistics', lambda: require(analytics.locator('#statMeanPrice').inner_text() != 'RM -', 'Mean price missing'))
            snapshot(analytics, 'analytics')
            check('analytics: desktop overflow', lambda: overflow(analytics))
            phone_analytics, _ = page_for('phone analytics', mobile=True)
            phone_analytics.goto(base + '/analytics.html', wait_until='domcontentloaded')
            check('analytics: phone overflow', lambda: overflow(phone_analytics))
            snapshot(phone_analytics, 'phone-analytics')

            cases = json.loads((ROOT / 'tests/fixtures/regressions.json').read_text(encoding='utf-8'))
            base_row = dict(cases['gaming_laptop'], url='https://example.com/laptop', series='Synthetic test store')
            fixture = [dict(base_row, id='ram16', title='Known RAM gaming'),
                       dict(base_row, id='unknown', title='Unknown RAM gaming', memory='', graphics='RTX 4060'),
                       dict(base_row, id='arc', title='Integrated Arc laptop', graphics='Intel Arc integrated graphics')]
            synthetic, _ = page_for('synthetic filter regressions', fixture=fixture)
            synthetic.goto(base + '/index.html', wait_until='domcontentloaded')
            expect(synthetic.locator('#grid .ticket')).to_have_count(3)
            synthetic.locator('#steamSpecBtn').click()
            check('BUG-07: Steam accepts system RAM despite VRAM', lambda: expect(synthetic.get_by_text('Known RAM gaming', exact=True)).to_be_visible())
            check('BUG-08: Steam excludes unknown RAM', lambda: expect(synthetic.get_by_text('Unknown RAM gaming', exact=True)).to_have_count(0))
            synthetic.locator('#resetBtn').click()
            synthetic.locator('[data-target="fg-gpu"]').click()
            synthetic.locator('#gpu-igpu').check()
            check('BUG-09: Integrated includes Intel Arc', lambda: expect(synthetic.get_by_text('Integrated Arc laptop', exact=True)).to_be_visible())

            more_fixture = [dict(base_row, id='solo', title='Single seller', memory='16GB DDR5', vendor_count=1),
                            dict(base_row, id='multi', title='Multi seller', memory='32GB DDR5', vendor_count=2,
                                 vendor_prices='Seller A: 4999 | Seller B: 5199', vendor_urls='Seller A: https://example.com/a | Seller B: https://example.com/b')]
            chips, _ = page_for('synthetic phone chips', mobile=True, fixture=more_fixture)
            chips.goto(base + '/mobile.html', wait_until='domcontentloaded')
            expect(chips.locator('.m-card')).to_have_count(2)
            chips.locator('#chipDeals').click()
            check('phone: multi-vendor chip excludes single-seller listings', lambda: expect(chips.get_by_text('Single seller', exact=True)).to_have_count(0))
            chips.locator('#chipAll').click()
            chips.locator('#chip16Gb').click()
            check('phone: 16GB+ chip includes 32GB configurations', lambda: expect(chips.get_by_text('Multi seller', exact=True)).to_be_visible())

            modules, _ = page_for('synthetic RAM display', fixture=[dict(base_row, id='modules', title='Dual module laptop', memory='8GB*2 DDR4-3200')])
            modules.goto(base + '/index.html', wait_until='domcontentloaded')
            check('desktop: two 8GB modules display 16GB installed RAM', lambda: expect(modules.locator('.spec-list li').filter(has_text='ram').locator('.spec-val')).to_have_text('16GB'))

            # A large synthetic catalog still uses the same validated/hash-checked loader.
            paged, _ = page_for('pagination', fixture=[dict(base_row,id=f'page-{i}',title=f'Pagination laptop {i}') for i in range(55)])
            paged.goto(base + '/index.html', wait_until='domcontentloaded')
            check('desktop: pagination loads the remaining verified configurations', lambda: (
                expect(paged.locator('#grid .ticket')).to_have_count(40), paged.locator('#loadMoreBtn').click(),
                expect(paged.locator('#grid .ticket')).to_have_count(55)))

            aged_release = fixture_release([dict(base_row,id='aged',title='Old verified laptop')],
                                           as_of=datetime.now(timezone.utc)-timedelta(days=8))
            aged, _ = page_for('expired offers')
            route_release(aged, aged_release)
            aged.goto(base + '/index.html', wait_until='domcontentloaded')
            check('expired offers: hidden by default and explicitly recoverable', lambda: (
                expect(aged.locator('#catalogMessage')).to_contain_text('1 offers older'),
                expect(aged.locator('#grid .ticket')).to_have_count(0), aged.locator('#showExpired').check(),
                expect(aged.locator('#grid .ticket')).to_have_count(1),
                expect(aged.locator('.offer-status')).to_contain_text('EXPIRED')))

            first_history = fixture_release([dict(base_row,id='history',title='Recorded laptop',price=5099)],
                                            as_of=datetime.now(timezone.utc)-timedelta(days=3))
            history_release = fixture_release([dict(base_row,id='history',title='Recorded laptop')], previous=first_history)
            history_page, _ = page_for('recorded history')
            route_release(history_page, history_release)
            history_page.goto(base + '/analytics.html', wait_until='domcontentloaded')
            check('history: only two actual points, no filled days', lambda: (
                expect(history_page.locator('#priceHistoryUnavailable')).to_have_text('2 recorded observations for this exact seller offer.'),
                expect(history_page.locator('#priceHistoryBody tbody tr')).to_have_count(2)))

            failure_page, _ = page_for('load failure and retry')
            for pattern in ('**/data/current.json', '**/data/data.js', '**/data/laptops.json', '**/*.csv'):
                failure_page.route(pattern, lambda route: route.fulfill(status=503,body='Unavailable'))
            failure_page.goto(base + '/index.html', wait_until='domcontentloaded')
            check('load failure: explicit error with no legacy catalog fallback', lambda: (
                expect(failure_page.locator('#catalogMessage')).to_have_text('Verified catalog could not be loaded. Please retry.'),
                expect(failure_page.locator('#catalogRetry')).to_be_visible(), expect(failure_page.locator('#grid .ticket')).to_have_count(0)))
            failure_page.unroute('**/data/current.json')
            route_rows(failure_page,[dict(base_row,id='retry',title='Recovered verified laptop')])
            check('load failure: retry recovers through verified endpoints', lambda: (
                failure_page.locator('#catalogRetry').click(), expect(failure_page.locator('#grid .ticket')).to_have_count(1),
                expect(failure_page.locator('#catalogRetry')).to_be_hidden()))

            for details in report['pages']:
                check(details['name'] + ': no JavaScript exceptions', lambda d=details: require(not d['errors'], str(d['errors'])))
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
        (output / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    failures = [item for item in report['checks'] if item['status'] == 'fail']
    print(json.dumps({'output_dir': str(output), 'passed': len(report['checks']) - len(failures), 'failed': len(failures), 'failures': failures}, indent=2))
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
