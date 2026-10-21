"""Re-read public product pages for a bounded audit of each enabled source."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import random
import sys
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))

import requests
from release_pipeline import atomic_write, digest, encoded, load_release
from source_audit import audit_allit_offer


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=ROOT/'data')
    parser.add_argument('--output', type=Path, default=ROOT/'artifacts/phase6-source/audit.json')
    args = parser.parse_args(argv)
    release = load_release(args.data_dir)
    if release is None:
        raise ValueError('No verified release')
    configs = {c['id']:c for c in release['catalog']['configurations']}
    offers_by_source = {}
    for offer in release['catalog']['offers']:
        offers_by_source.setdefault(offer['source_id'], []).append(offer)
    report = {'checked_at':datetime.now(timezone.utc).isoformat(), 'release_sha256':digest(release),
              'release_generated_at':release['generated_at'], 'sources':[]}
    session = requests.Session()
    session.headers['User-Agent'] = 'LaptopPicker/1.0 public source audit'
    cache = {}
    for source, offers in sorted(offers_by_source.items()):
        sample = sorted(offers, key=lambda o:o['id'])
        if len(sample) > 20:
            sample = random.Random(report['checked_at'][:10]).sample(sample,20)
        result = {'source_id':source, 'population':len(offers), 'sample_size':len(sample), 'offers':[]}
        for offer in sample:
            if source != 'allit':
                result['offers'].append({'offer_id':offer['id'], 'passed':False, 'error':'No source audit implementation'})
                continue
            u = urlsplit(offer['url'])
            if u.scheme != 'https' or u.hostname != 'www.allithypermarket.com.my' or not u.path.startswith('/products/'):
                raise ValueError('Source audit URL is outside the enabled source')
            url = urlunsplit((u.scheme,u.netloc,u.path,'',''))
            try:
                if url not in cache:
                    with session.get(url, timeout=(5,20), headers={'Accept':'text/html'}) as response:
                        response.raise_for_status()
                        html = response.text
                    with session.get(url+'.json', timeout=(5,20), headers={'Accept':'application/json'}) as response:
                        response.raise_for_status()
                        product = response.json()['product']
                    observed = datetime.now(timezone.utc).isoformat()
                    cache[url] = (product,html,observed)
                product,html,observed = cache[url]
                audit = audit_allit_offer(offer,configs[offer['configuration_id']],product,html)
                audit.update(checked_at=observed, product_url=url)
                result['offers'].append(audit)
            except (requests.RequestException, ValueError, KeyError) as error:
                result['offers'].append({'offer_id':offer['id'], 'passed':False, 'error':type(error).__name__, 'product_url':url})
        result['passed'] = bool(sample) and all(o['passed'] for o in result['offers'])
        report['sources'].append(result)
    report['passed'] = bool(report['sources']) and all(s['passed'] for s in report['sources'])
    atomic_write(args.output,encoded(report))
    print(json.dumps({'passed':report['passed'], 'sources':[{k:v for k,v in s.items() if k!='offers'} for s in report['sources']], 'output':str(args.output)},indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
