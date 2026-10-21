"""Open a fresh phase-specific ledger; never import the historical aggregate ledger."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from release_pipeline import atomic_write,encoded
from validation_runs import implementation_digest,new_gate,scoped_validation_status


def open_gate(folder,phase,environment):
    gate=new_gate(phase,implementation_digest(ROOT),environment)
    destination=Path(folder)/gate['gate_id']
    destination.mkdir(parents=True,exist_ok=False)
    atomic_write(destination/'gate.json',encoded(gate))
    return destination,gate


def read_receipts(folder):
    receipts=[]
    for path in sorted((Path(folder)/'receipts').glob('*.json')):
        try:receipts.append(json.loads(path.read_text(encoding='utf-8')))
        except (OSError,ValueError):receipts.append({})
    return receipts


def append_receipt(folder,evidence):
    folder=Path(folder);gate=json.loads((folder/'gate.json').read_text(encoding='utf-8'))
    code=implementation_digest(ROOT)
    if code!=gate['implementation_sha256']:raise ValueError('Implementation changed; open a fresh gate')
    steps=evidence.get('steps') or []
    if not steps or any(type(s.get('exit_code')) is not int or not s.get('name') for s in steps):
        raise ValueError('Actual named step outcomes are required')
    now=datetime.now(timezone.utc)
    receipt={'receipt_version':2,'gate_id':gate['gate_id'],'phase':gate['phase'],'environment':gate['environment'],
             'implementation_sha256':code,'started_at':evidence['started_at'],'recorded_at':now.isoformat(),
             'release_sha256':evidence.get('release_sha256'),'steps':steps,'healthy':all(s['exit_code']==0 for s in steps)}
    status=scoped_validation_status(gate,[receipt],code,as_of=now)
    if status['accepted_receipts']!=1:raise ValueError('Receipt does not belong to this gate')
    if receipt['healthy'] and not receipt['release_sha256']:raise ValueError('Healthy receipt needs a verified release')
    atomic_write(folder/'receipts'/(now.strftime('%Y%m%dT%H%M%S%fZ')+'.json'),encoded(receipt))
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['open','status'])
    p.add_argument('--phase',choices=['6R','7F'])
    p.add_argument('--environment',choices=['local','github-actions'],default='local')
    p.add_argument('--ledger-root',type=Path,default=ROOT/'artifacts/gates')
    p.add_argument('--gate-dir',type=Path)
    a=p.parse_args()
    if a.command=='open':
        if not a.phase:p.error('--phase is required to open a new gate')
        folder,gate=open_gate(a.ledger_root,a.phase,a.environment)
        print(json.dumps({'gate_dir':str(folder),**gate},indent=2))
    else:
        if not a.gate_dir:p.error('--gate-dir is required; aggregate ledgers are never scanned')
        gate=json.loads((a.gate_dir/'gate.json').read_text(encoding='utf-8'))
        print(json.dumps(scoped_validation_status(gate,read_receipts(a.gate_dir),implementation_digest(ROOT)),indent=2))
