"""Check actual hosted maintenance bytes and absence of catalog/diagnostic files."""
import argparse
import hashlib
import json
from pathlib import Path
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

EXCLUDED = ('data/current.json', 'js/core.js', 'LaptopScraper.exe',
            'data/catalog.v2.diagnostics.json', 'tests/fixtures/releases/phase6-2026-10-20/current.json')


def fetch(url):
    request = Request(url, headers={'Cache-Control': 'no-cache', 'User-Agent': 'LaptopPicker/1.0 deployment verification'})
    try:
        with urlopen(request, timeout=20) as response:
            return response.status, response.read(2_000_001)
    except HTTPError as error:
        return error.code, error.read(2_000_001)


def verify(base, manifest):
    base = base.rstrip('/') + '/'
    for name, digest in manifest['files'].items():
        status, body = fetch(base + name)
        if status != 200 or hashlib.sha256(body).hexdigest() != digest:
            raise ValueError(f'Unexpected status/content at {name}: HTTP {status}')
    status, body = fetch(base)
    if status != 200 or hashlib.sha256(body).hexdigest() != manifest['files']['index.html']:
        raise ValueError('Root does not serve expected maintenance bytes')
    for name in EXCLUDED:
        status, _ = fetch(base + name)
        if status != 404:
            raise ValueError(f'Excluded path must return 404: {name}, HTTP {status}')
    print('Hosted maintenance hashes and excluded-path checks passed.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--attempts', type=int, default=1)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
    for attempt in range(args.attempts):
        try:
            verify(args.url, manifest)
            break
        except (ValueError, OSError) as error:
            if attempt + 1 == args.attempts:
                raise
            print(f'Waiting for served deployment ({attempt + 1}/{args.attempts}): {error}')
            time.sleep(10)
