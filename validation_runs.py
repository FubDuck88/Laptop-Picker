"""Count observed local validation days without counting same-day reruns twice."""

from datetime import datetime, timedelta, timezone
import hashlib
import re
import uuid
from pathlib import Path


MALAYSIA = timezone(timedelta(hours=8))


def implementation_digest(root):
    root = Path(root)
    paths = set(root.glob('*.py')) | set(root.glob('*.html')) | {root/'requirements-test.txt',root/'requirements.txt',root/'ScrapeLaptops.bat',root/'.gitattributes'}
    for folder, patterns in [('js',('*.js',)),('css',('*.css',)),('schemas',('*.json',)),
                             ('scrapers',('*.py',)),('tools',('*.py',)),('tests',('*.py','*.cjs')),
                             ('.github/workflows',('*.yml','*.yaml'))]:
        for pattern in patterns:
            paths.update((root/folder).rglob(pattern))
    paths.update(p for p in (root/'tests/fixtures').rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    paths.update((root/'site/maintenance').glob('*'))
    paths.update((root/'deployments').glob('*.json'))
    hasher = hashlib.sha256()
    for path in sorted(paths):
        if path.is_file() and '__pycache__' not in path.parts:
            relative=path.relative_to(root).as_posix()
            payload=path.read_bytes()
            # Source line endings are canonical; frozen acceptance bytes remain exact.
            if not relative.startswith('tests/fixtures/'):
                payload=payload.replace(b'\r\n',b'\n')
            hasher.update(relative.encode()+b'\0'+payload+b'\0')
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
    return {'scope':'historical_phase6_only','implementation_sha256':code_sha256, 'checked_at':now.isoformat(),
            'timezone':'Asia/Kuala_Lumpur', 'required_days':7, 'consecutive_healthy_days':count,
            'latest_observed_day':latest.isoformat() if latest else None,
            'local_seven_day_gate_passed':count >= 7 and invalid == 0,
            'invalid_receipts':invalid, 'hosted_operation':'not_assessed_by_local_runner',
            'days':{d.isoformat():{'healthy':v[1],'recorded_at':v[0].isoformat()} for d,v in sorted(days.items())}}


def new_gate(phase,code_sha256,environment,*,as_of=None):
    now=as_of or datetime.now(timezone.utc)
    if phase not in ('6R','7F') or environment not in ('local','github-actions') or now.tzinfo is None:
        raise ValueError('Explicit phase, environment and timezone are required')
    if not re.fullmatch('[a-f0-9]{64}',code_sha256):raise ValueError('Invalid implementation fingerprint')
    return {'gate_version':1,'gate_id':uuid.uuid4().hex,'phase':phase,'environment':environment,
            'implementation_sha256':code_sha256,'started_at':now.isoformat()}


def scoped_validation_status(gate,receipts,code_sha256,*,as_of=None):
    now=as_of or datetime.now(timezone.utc)
    start=datetime.fromisoformat(gate['started_at'])
    if now.tzinfo is None or start.tzinfo is None or start>now:raise ValueError('Invalid gate clock')
    if (gate.get('gate_version')!=1 or gate.get('phase') not in ('6R','7F')
            or gate.get('environment') not in ('local','github-actions')
            or not re.fullmatch('[a-f0-9]{32}',gate.get('gate_id',''))):
        raise ValueError('Invalid gate identity/version')
    excluded={};valid=[];invalid_current=0
    def exclude(reason):excluded[reason]=excluded.get(reason,0)+1
    changed=gate['implementation_sha256']!=code_sha256
    for receipt in receipts:
        reason=None
        for field,expected in [('receipt_version',2),('gate_id',gate['gate_id']),('phase',gate['phase']),
                               ('environment',gate['environment']),('implementation_sha256',gate['implementation_sha256'])]:
            if receipt.get(field)!=expected:reason='wrong_'+field;break
        if changed:reason='implementation_changed'
        if reason:
            exclude(reason)
            if receipt.get('gate_id')==gate['gate_id']:invalid_current+=1
            continue
        try:
            began=datetime.fromisoformat(receipt['started_at']);recorded=datetime.fromisoformat(receipt['recorded_at'])
            if began.tzinfo is None or recorded.tzinfo is None or began>recorded or recorded>now:
                raise ValueError('Invalid receipt time')
            if began<start or recorded<start:
                exclude('before_gate_start');invalid_current+=1;continue
        except (KeyError,TypeError,ValueError):
            exclude('invalid_time');invalid_current+=1;continue
        valid.append({**receipt,'receipt_version':1,'environment':'local'})
    counted=local_validation_status(valid,gate['implementation_sha256'],as_of=now)
    days=counted['consecutive_healthy_days'] if gate['phase']=='7F' else 0
    return {'gate_id':gate['gate_id'],'phase':gate['phase'],'environment':gate['environment'],
            'started_at':gate['started_at'],'implementation_sha256':code_sha256,'reset_required':changed,
            'consecutive_healthy_days':days,'required_days':7 if gate['phase']=='7F' else None,
            'validation_window_passed':gate['phase']=='7F' and not changed and not invalid_current and days>=7,
            'accepted_receipts':len(valid),'excluded_receipts':excluded,'checked_at':now.isoformat(),
            'invalid_current_receipts':invalid_current,
            'scope':'operational_only' if gate['phase']=='6R' else 'integrated_release_validation'}
