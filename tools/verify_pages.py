"""Verify hosted artifact bytes, real browser loading and controlled failure detection."""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urljoin
import sys
import time
import requests
from playwright.sync_api import sync_playwright


def verify(base, manifest, *, fault=None):
    base=base.rstrip('/')+'/'
    session=requests.Session()
    for name,expected in manifest['files'].items():
        response=session.get(urljoin(base,name),timeout=(10,25),headers={'Cache-Control':'no-cache'})
        if response.status_code != 200 or hashlib.sha256(response.content).hexdigest()!=expected:
            raise ValueError('Served artifact mismatch: '+name)
    for excluded in ['tests/fixtures/source_snapshots.json','data/catalog.v2.diagnostics.json','LaptopScraper.exe']:
        if session.get(urljoin(base,excluded),timeout=(10,25)).status_code != 404:
            raise ValueError('Excluded path is served: '+excluded)
    prefix=manifest.get('candidate_prefix','')
    expected_sha=manifest['release_sha256']
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        try:
            for name,mobile in [('index.html?desktop=1',False),('mobile.html',True),('analytics.html',False)]:
                page=browser.new_page(viewport={'width':390 if mobile else 1440,'height':900},is_mobile=mobile)
                errors=[]; escaped=[]
                page.on('pageerror',lambda e:errors.append(str(e)))
                if prefix:
                    page.on('request',lambda r:escaped.append(r.url) if '/data/' in r.url and r.url.startswith(base) and not r.url.startswith(urljoin(base,prefix)) else None)
                if fault=='http': page.route('**/data/current.json',lambda r:r.fulfill(status=503,body='unavailable'))
                if fault=='hash': page.route('**/data/releases/*.json',lambda r:r.fulfill(content_type='application/json',body='{}'))
                if fault=='frontend': page.add_init_script('throw new Error("Controlled frontend failure")')
                page.goto(urljoin(base,prefix+name),wait_until='domcontentloaded')
                page.wait_for_function('typeof loadVerifiedRelease === "function"',timeout=15000)
                actual=page.evaluate('async () => { const r=await loadVerifiedRelease(); return {count:r.catalog.offers.length, freshness:Object.keys(r.freshness).length}; }')
                if errors or escaped or actual['count']<1 or actual['freshness']!=actual['count']:
                    raise ValueError('Frontend loading or candidate data boundary failed')
                pointer=page.evaluate('async () => (await (await fetch("data/current.json",{cache:"no-store"})).json()).sha256')
                if pointer!=expected_sha:raise ValueError('Wrong served release')
                page.route('**/data/releases/*.json',lambda r:r.fulfill(content_type='application/json',body='{}'))
                rejected=page.evaluate('async()=>{try{await loadVerifiedRelease();return false;}catch(e){return e.message.includes("integrity");}}')
                if not rejected:raise ValueError('Corrupt payload was not rejected')
                page.close()
        finally:browser.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url',required=True)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--drill',action='store_true')
    a=parser.parse_args();m=json.loads(a.manifest.read_text(encoding='utf-8'))
    for attempt in range(6):
        try:
            verify(a.url,m)
            break
        except Exception as error:
            if attempt == 5:raise
            print('Waiting for hosted artifact propagation: '+type(error).__name__,flush=True)
            time.sleep(10)
    if a.drill:
        detected=[]
        for fault in ['http','hash','frontend']:
            try:verify(a.url,m,fault=fault)
            except Exception:
                detected.append(fault)
                print('Controlled '+fault+' failure detected.',flush=True)
            else:raise ValueError('Controlled '+fault+' failure escaped detection')
        Path('artifacts/pages/drill.json').write_text(json.dumps({'baseline_verified':True,'detected':detected})+'\n')
        print('All controlled failures detected; forcing the hosted recovery path.',flush=True)
        sys.exit(2)
    print('Hosted artifact bytes, frontends, candidate isolation and corruption rejection passed.')
