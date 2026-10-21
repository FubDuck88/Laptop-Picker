"""Collect and atomically activate a validated v2 release; legacy website data is untouched."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))

from release_pipeline import (activate_release, atomic_write, build_release, collection_lock, encoded,
                              load_release, publish_release)
from source_adapters import SOURCE_IDS, collect_sources
from photo_validation import validate_source_photos


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', nargs='+', choices=SOURCE_IDS, default=['allit'])
    parser.add_argument('--data-dir', type=Path, default=ROOT / 'data')
    parser.add_argument('--diagnostics-dir', type=Path, default=ROOT / 'artifacts' / 'collection')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--validate', action='store_true', help='Read and validate the active release without collecting or writing')
    mode.add_argument('--activate', help='Explicitly activate a retained releases/SHA256.json file for rollback')
    args = parser.parse_args(argv)
    try:
        if args.validate:
            release = load_release(args.data_dir)
            if release is None:
                raise ValueError('No active verified release')
            print(f"Valid release: {len(release['catalog']['offers'])} offers")
            return 0
        with collection_lock(args.data_dir):
            if args.activate:
                release = activate_release(args.data_dir, args.activate)
                print(f"Activated retained release observed at {release['generated_at']}; observation times were preserved")
                return 0
            previous = load_release(args.data_dir)
            results = collect_sources(args.sources)
            results, photo_checks = validate_source_photos(results, previous)
            atomic_write(args.diagnostics_dir / 'photos.json', encoded(photo_checks))
            release, diagnostics = build_release(results, previous)
            atomic_write(args.diagnostics_dir / 'diagnostics.json', encoded(diagnostics))
            atomic_write(args.diagnostics_dir / 'run.json', encoded({
                'generated_at': release['generated_at'], 'attempts': release['attempts'],
                'source_decisions': release['source_decisions'], 'freshness': release['freshness']}))
            pointer = publish_release(release, args.data_dir)
            print(f"Activated {pointer['path']}: {len(release['catalog']['offers'])} accepted or retained offers")
            for decision in release['source_decisions']:
                print(f"{decision['source_id']}: {decision['state']}" + (f" ({decision['reason']})" if decision['reason'] else ''))
            healthy = all(d['state'] == 'updated' for d in release['source_decisions'] if d['source_id'] in args.sources)
            atomic_write(args.diagnostics_dir / 'status.json', encoded({'observed_at': release['generated_at'], 'healthy': healthy, 'active_release': pointer['path'], 'error': None if healthy else 'One or more sources were retained or unavailable'}))
            return 0 if healthy else 1
    except (ValueError, OSError, KeyError, TypeError) as error:
        if not args.validate:
            atomic_write(args.diagnostics_dir / 'status.json', encoded({'observed_at': datetime.now(timezone.utc).isoformat(), 'healthy': False, 'active_release': None, 'error': str(error)}))
        print(f'Publication failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
