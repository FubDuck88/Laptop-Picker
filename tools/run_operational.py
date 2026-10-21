"""One actual 6R operational check; no receipt from this runner can count for 7F."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import re
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT))
from gate_ledger import open_gate,append_receipt,read_receipts
from release_pipeline import load_release,digest,atomic_write,encoded
from validation_runs import implementation_digest,MALAYSIA,scoped_validation_status


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--if-needed',action='store_true')
    a=p.parse_args()
    ledgers=ROOT/'artifacts/gates';pointer=ledgers/'current-6r-local.json'
    folder=gate=None
    if pointer.exists():
        identity=json.loads(pointer.read_text(encoding='utf-8'))['gate_id']
        if not re.fullmatch('[a-f0-9]{32}',identity):raise ValueError('Invalid local gate pointer')
        folder=ledgers/identity;gate=json.loads((folder/'gate.json').read_text(encoding='utf-8'))
        if gate['phase']!='6R' or gate['environment']!='local':raise ValueError('Operational runner requires a local 6R gate')
    code=implementation_digest(ROOT)
    if gate is None or gate['implementation_sha256']!=code:
        folder,gate=open_gate(ledgers,'6R','local')
        atomic_write(pointer,encoded({'gate_id':gate['gate_id']}))
    receipts=read_receipts(folder)
    release=load_release(ROOT/'data')
    today=datetime.now(timezone.utc).astimezone(MALAYSIA).date()
    latest=max(receipts,key=lambda r:r.get('recorded_at',''),default={})
    reused=(a.if_needed and latest.get('healthy') is True and release
            and latest.get('release_sha256')==digest(release)
            and datetime.fromisoformat(latest['recorded_at']).astimezone(MALAYSIA).date()==today)
    if reused:
        print(json.dumps({'reused_today':True,'healthy':True,'gate_dir':str(folder)}));return 0
    start=datetime.now(timezone.utc)
    output=ROOT/'artifacts/operational'/start.strftime('%Y%m%dT%H%M%S%fZ')
    output.mkdir(parents=True,exist_ok=False)
    commands=[('offline',['tools/check.py']),
              ('collection',['tools/run_daily.py','--sources','allit','--diagnostics-dir',str(output/'collection')]),
              ('release',['tools/run_daily.py','--validate']),
              ('source_audit',['tools/audit_source_release.py','--output',str(output/'source-audit.json')]),
              ('browser',['tools/browser_smoke.py','--output-dir',str(output/'browser')]),
              ('responsive',['tools/check_responsive.py','--output',str(output/'responsive.json')]),
              ('photos',['tools/check_photos_browser.py'])]
    steps=[]
    for name,args in commands:
        print('Checking '+name+'...',flush=True)
        try:
            result=subprocess.run([sys.executable,'-B',*args],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=900)
            exit_code,log=result.returncode,result.stdout
        except (OSError,subprocess.TimeoutExpired) as e:
            exit_code,log=1,(type(e).__name__+': '+str(e)).encode()
        atomic_write(output/(name+'.log'),log[:2*1024*1024])
        steps.append({'name':name,'exit_code':exit_code})
        if exit_code:break
    release=load_release(ROOT/'data')
    receipt=append_receipt(folder,{'started_at':start.isoformat(),'steps':steps,'release_sha256':digest(release) if release else None})
    status={'healthy':receipt['healthy'],'reused_today':False,'gate_dir':str(folder),
            'evidence_dir':str(output),'release_sha256':receipt['release_sha256'],
            **scoped_validation_status(gate,read_receipts(folder),implementation_digest(ROOT))}
    atomic_write(ROOT/'artifacts/operational/status.json',encoded(status))
    print(json.dumps(status,indent=2))
    return 0 if receipt['healthy'] else 1


if __name__=='__main__':raise SystemExit(main())
