"""Count observed local validation days without counting same-day reruns twice."""

from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path


MALAYSIA = timezone(timedelta(hours=8))


def implementation_digest(root):
    root = Path(root)
    paths = set(root.glob('*.py')) | set(root.glob('*.html')) | {root/'requirements-test.txt',root/'requirements.txt'}
    for folder, patterns in [('js',('*.js',)),('css',('*.css',)),('schemas',('*.json',)),
                             ('scrapers',('*.py',)),('tools',('*.py',)),('tests',('*.py','*.cjs')),
                             ('.github/workflows',('*.yml','*.yaml'))]:
        for pattern in patterns:
            paths.update((root/folder).glob(pattern))
    hasher = hashlib.sha256()
    for path in sorted(paths):
        if path.is_file():
            hasher.update(path.relative_to(root).as_posix().encode()+b'\0'+path.read_bytes()+b'\0')
    return hasher.hexdigest()


def local_validation_status(receipts, code_sha256, *, as_of=None):
    now = as_of or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError('Validation clock requires a timezone')
    days = {}
    invalid = 0
    for receipt in receipts:
        try:
            recorded = datetime.fromisoformat(receipt['recorded_at'].replace('Z','+00:00'))
            if recorded.tzinfo is None or recorded > now or receipt['receipt_version'] != 1:
                raise ValueError('Invalid receipt time/version')
            if receipt['implementation_sha256'] != code_sha256 or receipt['environment'] != 'local':
                continue
            day = recorded.astimezone(MALAYSIA).date()
            prior = days.get(day)
            if prior is None or recorded > prior[0]:
                days[day] = (recorded, receipt.get('healthy') is True)
        except (KeyError, TypeError, ValueError):
            invalid += 1
    today = now.astimezone(MALAYSIA).date()
    latest = max(days) if days else None
    count = 0
    if latest is not None and latest >= today-timedelta(days=1):
        day = latest
        while day in days and days[day][1]:
            count += 1
            day -= timedelta(days=1)
    return {'implementation_sha256':code_sha256, 'checked_at':now.isoformat(),
            'timezone':'Asia/Kuala_Lumpur', 'required_days':7, 'consecutive_healthy_days':count,
            'latest_observed_day':latest.isoformat() if latest else None,
            'local_seven_day_gate_passed':count >= 7 and invalid == 0,
            'invalid_receipts':invalid, 'hosted_operation':'not_assessed_by_local_runner',
            'days':{d.isoformat():{'healthy':v[1],'recorded_at':v[0].isoformat()} for d,v in sorted(days.items())}}
