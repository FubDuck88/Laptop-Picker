"""Perform one real local validation run and persist its actual outcome.

Seven distinct consecutive Malaysia dates are required for the local gate. This
does not certify a hosted workflow or deploy the site.
"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))

from release_pipeline import atomic_write, digest, encoded, load_release
from validation_runs import implementation_digest, local_validation_status, MALAYSIA


def read_receipts(folder):
    receipts = []
    for path in sorted(folder.glob('*/receipt.json')):
        try:
            receipts.append(json.loads(path.read_text(encoding='utf-8')))
        except (ValueError, OSError):
            receipts.append({})
    return receipts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ledger-dir', type=Path, default=ROOT/'artifacts/phase6-observation')
    parser.add_argument('--status', action='store_true', help='Recalculate progress without collecting or running tests')
    parser.add_argument('--if-needed', action='store_true', help='Reuse a healthy check of the same implementation/release on the same local date')
    args = parser.parse_args(argv)
    now = datetime.now(timezone.utc)
    code = implementation_digest(ROOT)
    receipts = read_receipts(args.ledger_dir)
    status = local_validation_status(receipts,code,as_of=now)
    active = load_release(ROOT/'data')
    today = now.astimezone(MALAYSIA).date()
    latest = max((r for r in receipts if r.get('implementation_sha256') == code),key=lambda r:r.get('recorded_at',''),default={})
    reused = bool(args.if_needed and latest.get('healthy') and active and latest.get('release_sha256') == digest(active)
                  and datetime.fromisoformat(latest['recorded_at']).astimezone(MALAYSIA).date() == today)
    if args.status or reused:
        atomic_write(args.ledger_dir/'status.json',encoded(status))
        print(json.dumps({'reused_today':reused,**status},indent=2))
        return 0 if not status['invalid_receipts'] else 1
    run_dir = args.ledger_dir/now.strftime('%Y%m%dT%H%M%S%fZ')
    run_dir.mkdir(parents=True,exist_ok=False)
    steps = []
    commands = [
        ('offline',[sys.executable,'-B','tools/check.py']),
        ('collection',[sys.executable,'-B','tools/run_daily.py','--sources','allit','--diagnostics-dir',str(run_dir/'collection')]),
        ('release_validation',[sys.executable,'-B','tools/run_daily.py','--validate']),
        ('source_audit',[sys.executable,'-B','tools/audit_source_release.py','--output',str(run_dir/'source-audit.json')]),
        ('browser',[sys.executable,'-B','tools/browser_smoke.py','--output-dir',str(run_dir/'browser')]),
        ('responsive',[sys.executable,'-B','tools/check_responsive.py','--output',str(run_dir/'responsive.json')]),
        ('photos',[sys.executable,'-B','tools/check_photos_browser.py']),
    ]
    for name, command in commands:
        print('Checking '+name+'...',flush=True)
        try:
            response = subprocess.run(command,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=900,check=False)
            code_value, output = response.returncode, response.stdout
        except (subprocess.TimeoutExpired, OSError) as error:
            code_value, output = 1, (type(error).__name__+': '+str(error)).encode()
        atomic_write(run_dir/(name+'.log'),output[:2*1024*1024])
        steps.append({'name':name,'exit_code':code_value})
        if code_value:
            break
    active = load_release(ROOT/'data')
    healthy = len(steps) == len(commands) and all(s['exit_code'] == 0 for s in steps)
    healthy = healthy and active is not None and implementation_digest(ROOT) == code
    audit, browser, responsive = None, None, None
    if healthy:
        audit = json.loads((run_dir/'source-audit.json').read_text(encoding='utf-8'))
        browser = json.loads((run_dir/'browser/report.json').read_text(encoding='utf-8'))
        responsive = json.loads((run_dir/'responsive.json').read_text(encoding='utf-8'))
        healthy = (audit['passed'] is True and audit['release_sha256'] == digest(active)
                   and bool(browser['checks']) and all(c['status'] == 'pass' for c in browser['checks'])
                   and bool(responsive['checks']) and all(c['passed'] for c in responsive['checks'])
                   and all(d['state'] == 'updated' for d in active['source_decisions']))
    receipt = {'receipt_version':1, 'environment':'local', 'started_at':now.isoformat(),
               'recorded_at':datetime.now(timezone.utc).isoformat(), 'implementation_sha256':code,
               'release_sha256':digest(active) if active else None, 'healthy':bool(healthy), 'steps':steps,
               'audit_population':sum(s['population'] for s in audit['sources']) if audit else None,
               'audited_offers':sum(s['sample_size'] for s in audit['sources']) if audit else None,
               'browser_checks':len(browser['checks']) if browser else None,
               'responsive_checks':len(responsive['checks']) if responsive else None}
    atomic_write(run_dir/'receipt.json',encoded(receipt))
    status = local_validation_status([*receipts,receipt],code)
    atomic_write(args.ledger_dir/'status.json',encoded(status))
    print(json.dumps({'healthy':bool(healthy),'receipt':str(run_dir/'receipt.json'),**status},indent=2))
    return 0 if healthy else 1


if __name__ == '__main__':
    raise SystemExit(main())
