"""Inspect actual catalog/detail layouts at phone, tablet and desktop widths."""

import argparse
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*args):
        pass

    def copyfile(self,source,outputfile):
        try:
            super().copyfile(source,outputfile)
        except (ConnectionAbortedError,BrokenPipeError):
            pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'artifacts/phase6-responsive/report.json')
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(ROOT)))
    Thread(target=server.serve_forever,daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}'
    report = {'checked_at':datetime.now(timezone.utc).isoformat(),'checks':[]}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            for width in (320,375,390,768,1024,1440):
                for path in ('index.html','analytics.html'):
                    page = browser.new_page(viewport={'width':width,'height':900})
                    entry = {'width':width,'path':path,'errors':[],'passed':False}
                    page.on('pageerror',lambda e:entry['errors'].append(str(e)))
                    try:
                        page.goto(base+'/'+path,wait_until='domcontentloaded')
                        page.wait_for_function('document.getElementById("catalogMessage").textContent.includes("verified configurations")',timeout=10000)
                        page.evaluate('document.fonts.ready')
                        def overflow():
                            return page.evaluate('({viewport:document.documentElement.clientWidth, content:document.documentElement.scrollWidth})')
                        entry['layout'] = overflow()
                        buttons = page.locator('.m-detail-btn' if width <= 768 else '.detail-btn')
                        if path == 'analytics.html':
                            page.locator('#analyticsTableBody tr').first.click()
                        elif buttons.count():
                            buttons.first.click()
                        entry['detail_layout'] = overflow()
                        entry['passed'] = (all(entry[k]['content'] <= entry[k]['viewport']+1 for k in ('layout','detail_layout')) and not entry['errors'])
                    except Exception as error:
                        entry['error'] = str(error)[:800]
                    report['checks'].append(entry)
                    page.close()
            browser.close()
    finally:
        server.shutdown(); server.server_close()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':sum(c['passed'] for c in report['checks']),'total':len(report['checks']),
                      'failures':[c for c in report['checks'] if not c['passed']]},indent=2))
    return int(any(not c['passed'] for c in report['checks']))


if __name__ == '__main__':
    raise SystemExit(main())
