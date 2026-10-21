"""Validated, immutable releases with source recovery and real observation receipts."""

from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

from catalog_v2 import build_catalog, validate_catalog


POLICY = {'stale_after_hours': 48, 'expire_after_days': 7, 'history_days': 90}
MAX_RELEASE_BYTES = 40 * 1024 * 1024


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('Timestamp requires a timezone')
    return parsed


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf-8')


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def freshness(offer, as_of):
    age = (timestamp(as_of) - timestamp(offer['observed_at'])).total_seconds()
    if age < 0:
        raise ValueError('Offer is newer than the release')
    state = 'expired' if age >= 7 * 86400 else 'stale' if age >= 48 * 3600 else 'fresh'
    return {'state': state, 'show_by_default': state != 'expired', 'age_seconds': int(age)}


def source_slice(catalog, source_id):
    offers = [o for o in catalog['offers'] if o['source_id'] == source_id]
    ids = {o['id'] for o in offers}
    configs = {o['configuration_id'] for o in offers}
    return {'schema_version': 2, 'generated_at': catalog['generated_at'],
            'offers': offers, 'configurations': [c for c in catalog['configurations'] if c['id'] in configs],
            'observations': [o for o in catalog['observations'] if o['offer_id'] in ids],
            'run_reports': [r for r in catalog['run_reports'] if r['source_id'] == source_id]}


def build_release(results, previous=None, *, generated_at=None):
    generated_at = generated_at or datetime.now(timezone.utc).isoformat()
    generated = timestamp(generated_at)
    if previous:
        validate_release(previous)
        if generated < timestamp(previous['generated_at']):
            raise ValueError('Cannot publish an older release over a newer one')
    incoming = build_catalog(results, generated_at=generated_at)
    old = previous['catalog'] if previous else build_catalog([], generated_at=generated_at).catalog
    attempts = incoming.catalog['run_reports']
    attempt_map = {r['source_id']: r for r in attempts}
    sources = sorted(set(attempt_map) | {r['source_id'] for r in old['run_reports']})
    selected, decisions, accepted = [], [], set()
    for source_id in sources:
        current, prior = source_slice(incoming.catalog, source_id), source_slice(old, source_id)
        report = attempt_map.get(source_id)
        reason = None
        if report is None:
            reason = 'Source was not selected in this run'
        elif report['status'] != 'complete' or report['mode'] != 'live':
            reason = report['error'] or 'Source did not complete'
        elif not current['offers']:
            reason = 'No accepted offers; empty results cannot replace a good source'
        elif prior['offers'] and len(current['offers']) < len(prior['offers']) * 0.5:
            reason = 'Accepted offer count fell by more than 50%; source retained for review'
        elif prior['offers'] and min(timestamp(o['observed_at']) for o in current['offers']) < max(timestamp(o['observed_at']) for o in prior['offers']):
            reason = 'Source observations moved backwards in time'
        if reason is None:
            selected.append(current)
            accepted.add(source_id)
            decisions.append({'source_id': source_id, 'state': 'updated', 'reason': None})
        else:
            selected.append(prior if prior['run_reports'] else current)
            decisions.append({'source_id': source_id, 'state': 'retained' if prior['offers'] else 'unavailable', 'reason': reason})
    catalog = build_catalog([], generated_at=generated_at).catalog
    for name in ('configurations', 'offers', 'observations', 'run_reports'):
        catalog[name] = [deepcopy(row) for part in selected for row in part[name]]
    validate_catalog(catalog)
    history = deepcopy(previous['history']) if previous else {'configurations': {}, 'runs': {}, 'receipts': []}
    receipts = {r['observation']['id']: r for r in history['receipts']}
    configs = {c['id']: c for c in catalog['configurations']}
    offers = {o['id']: o for o in catalog['offers']}
    reports = {r['source_id']: r for r in catalog['run_reports']}
    for observation in catalog['observations']:
        offer = offers[observation['offer_id']]
        if offer['source_id'] not in accepted:
            continue
        run = reports[offer['source_id']]
        run_id = digest(run)
        history['runs'][run_id] = deepcopy(run)
        history['configurations'].setdefault(offer['configuration_id'], deepcopy(configs[offer['configuration_id']]))
        receipt = {'observation': deepcopy(observation), 'offer': deepcopy(offer), 'run_id': run_id}
        existing = receipts.get(observation['id'])
        if existing and existing['observation'] != observation:
            # Equal instants can have different RFC3339 spellings, but never different states.
            same = all(existing['observation'][key] == observation[key] for key in ('offer_id', 'configuration_id', 'price_sen', 'currency', 'availability'))
            if not same or timestamp(existing['observation']['observed_at']) != timestamp(observation['observed_at']):
                raise ValueError('Conflicting historical observation')
        receipts.setdefault(observation['id'], receipt)
    cutoff = generated - timedelta(days=POLICY['history_days'])
    history['receipts'] = sorted((r for r in receipts.values() if timestamp(r['observation']['observed_at']) >= cutoff), key=lambda r: (timestamp(r['observation']['observed_at']), r['observation']['id']))
    used_configs = {r['offer']['configuration_id'] for r in history['receipts']}
    used_runs = {r['run_id'] for r in history['receipts']}
    history['configurations'] = {k: v for k, v in history['configurations'].items() if k in used_configs}
    history['runs'] = {k: v for k, v in history['runs'].items() if k in used_runs}
    release = {'release_version': 1, 'generated_at': generated_at, 'policy': deepcopy(POLICY), 'catalog': catalog,
               'attempts': deepcopy(attempts), 'source_decisions': decisions, 'history': history,
               'freshness': {o['id']: freshness(o, generated_at) for o in catalog['offers']}}
    validate_release(release)
    return release, incoming.diagnostics


def validate_release(release):
    required = {'release_version', 'generated_at', 'policy', 'catalog', 'attempts', 'source_decisions', 'history', 'freshness'}
    if set(release) != required or release['release_version'] != 1 or release['policy'] != POLICY:
        raise ValueError('Invalid release format or freshness policy')
    generated = timestamp(release['generated_at'])
    validate_catalog(release['catalog'])
    if release['catalog']['generated_at'] != release['generated_at']:
        raise ValueError('Release and catalog build times differ')
    current_runs = {run['source_id']: run for run in release['catalog']['run_reports']}
    for offer in release['catalog']['offers']:
        run = current_runs[offer['source_id']]
        if run['mode'] != 'live' or run['status'] != 'complete' or not timestamp(run['started_at']) <= timestamp(offer['observed_at']) <= timestamp(run['finished_at']):
            raise ValueError('Current offers require their original successful source run')
    attempts = build_catalog([], generated_at=release['generated_at']).catalog
    attempts['run_reports'] = release['attempts']
    validate_catalog(attempts)
    if release['freshness'] != {o['id']: freshness(o, release['generated_at']) for o in release['catalog']['offers']}:
        raise ValueError('Freshness metadata disagrees with actual observation times')
    history = release['history']
    if set(history) != {'configurations', 'runs', 'receipts'}:
        raise ValueError('Invalid observation history')
    seen, instants, configs, runs = set(), set(), set(), set()
    for receipt in history['receipts']:
        if set(receipt) != {'observation', 'offer', 'run_id'}:
            raise ValueError('Invalid history receipt')
        offer, observation = receipt['offer'], receipt['observation']
        run = history['runs'][receipt['run_id']]
        configuration = history['configurations'][offer['configuration_id']]
        if receipt['run_id'] != digest(run) or run['status'] != 'complete' or run['mode'] != 'live':
            raise ValueError('History needs an actual successful source run')
        if not timestamp(run['started_at']) <= timestamp(observation['observed_at']) <= timestamp(run['finished_at']):
            raise ValueError('Historical observation falls outside its source run')
        if timestamp(observation['observed_at']) < generated - timedelta(days=POLICY['history_days']):
            raise ValueError('History exceeds the configured retention')
        single = {'schema_version': 2, 'generated_at': release['generated_at'], 'configurations': [configuration],
                  'offers': [offer], 'observations': [observation], 'run_reports': [run]}
        validate_catalog(single)
        if observation['id'] in seen:
            raise ValueError('Duplicate historical observation')
        instant = (observation['offer_id'], timestamp(observation['observed_at']))
        if instant in instants:
            raise ValueError('Duplicate historical offer instant')
        instants.add(instant)
        seen.add(observation['id'])
        configs.add(configuration['id'])
        runs.add(receipt['run_id'])
    if configs != set(history['configurations']) or runs != set(history['runs']):
        raise ValueError('Orphan historical metadata')
    for observation in release['catalog']['observations']:
        if timestamp(observation['observed_at']) >= generated - timedelta(days=POLICY['history_days']) and observation['id'] not in seen:
            raise ValueError('Current observation is missing its proof receipt')
    source_ids = {r['source_id'] for r in release['catalog']['run_reports']}
    decisions = release['source_decisions']
    if len(decisions) != len(source_ids) or {d['source_id'] for d in decisions} != source_ids:
        raise ValueError('Every retained or attempted source needs one decision')
    for decision in decisions:
        if set(decision) != {'source_id', 'state', 'reason'} or decision['state'] not in {'updated', 'retained', 'unavailable'}:
            raise ValueError('Invalid source decision')
        if (decision['state'] == 'updated') != (decision['reason'] is None):
            raise ValueError('Source retention requires an explanation')
        if decision['state'] == 'updated':
            attempt = next((r for r in release['attempts'] if r['source_id'] == decision['source_id']), None)
            if not attempt or attempt['mode'] != 'live' or attempt['status'] != 'complete' or not attempt['accepted_count']:
                raise ValueError('Updated source needs a successful accepted collection attempt')


def atomic_write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.release-', suffix='.tmp', delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def load_release(data_dir):
    root = Path(data_dir)
    pointer = root / 'current.json'
    if not pointer.exists():
        return None
    value = json.loads(pointer.read_text(encoding='utf-8'))
    if set(value) != {'release_version', 'path', 'sha256'} or value['release_version'] != 1 or not re.fullmatch(r'releases/[0-9a-f]{64}\.json', value['path']):
        raise ValueError('Invalid release pointer')
    payload = (root / value['path']).read_bytes()
    if hashlib.sha256(payload).hexdigest() != value['sha256'] or value['path'] != 'releases/' + value['sha256'] + '.json':
        raise ValueError('Release integrity check failed')
    release = json.loads(payload)
    validate_release(release)
    return release


def publish_release(release, data_dir):
    validate_release(release)
    if not release['catalog']['offers']:
        raise ValueError('No accepted or retained offers; publication refused')
    root = Path(data_dir)
    previous = load_release(root)
    previous_path = json.loads((root / 'current.json').read_text(encoding='utf-8'))['path'] if previous else None
    if previous and timestamp(previous['generated_at']) > timestamp(release['generated_at']):
        raise ValueError('A newer release is already published')
    payload = encoded(release)
    if len(payload) > MAX_RELEASE_BYTES:
        raise ValueError('Release exceeds the 40 MiB publication budget; existing release preserved')
    checksum = hashlib.sha256(payload).hexdigest()
    path = root / 'releases' / (checksum + '.json')
    if path.exists() and path.read_bytes() != payload:
        raise ValueError('Immutable release content differs')
    if not path.exists():
        atomic_write(path, payload)
    pointer = {'release_version': 1, 'path': 'releases/' + path.name, 'sha256': checksum}
    # This is the only switch readers need. A failed write leaves the old release active.
    atomic_write(root / 'current.json', encoded(pointer))
    # Keep the active file and its immediate predecessor for rollback. Receipt history
    # is self-contained in each release; removing older release files loses no retained prices.
    keep = {pointer['path'], previous_path}
    release_root = (root / 'releases').resolve()
    for old in release_root.glob('*.json'):
        if old.resolve().parent != release_root or not re.fullmatch(r'[0-9a-f]{64}\.json', old.name):
            continue
        if 'releases/' + old.name not in keep:
            try:
                if hashlib.sha256(old.read_bytes()).hexdigest() + '.json' == old.name:
                    old.unlink()
            except OSError:
                pass  # Retention cleanup cannot invalidate an already activated release.
    return pointer


def activate_release(data_dir, relative_path):
    """Explicit operator rollback; never used automatically after collection failure."""
    if not re.fullmatch(r'releases/[0-9a-f]{64}\.json', relative_path):
        raise ValueError('Select a retained immutable release path')
    root = Path(data_dir)
    payload = (root / relative_path).read_bytes()
    checksum = hashlib.sha256(payload).hexdigest()
    if relative_path != 'releases/' + checksum + '.json':
        raise ValueError('Rollback release integrity check failed')
    release = json.loads(payload)
    validate_release(release)
    if not release['catalog']['offers']:
        raise ValueError('Cannot activate an empty release')
    atomic_write(root / 'current.json', encoded({'release_version': 1, 'path': relative_path, 'sha256': checksum}))
    return release


@contextmanager
def collection_lock(data_dir):
    root = Path(data_dir)
    root.mkdir(parents=True, exist_ok=True)
    path = root / '.collection.lock'
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(descriptor, str(os.getpid()).encode('ascii'))
        yield
    finally:
        os.close(descriptor)
        path.unlink()
