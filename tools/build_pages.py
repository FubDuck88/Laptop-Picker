"""Build separate checked public and same-site candidate packages."""
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from pages_package import build

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-dir',type=Path,default=ROOT/'data')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--identity',required=True)
    p.add_argument('--recovery-archive',type=Path,required=True)
    p.add_argument('--recovery-sha',required=True)
    a=p.parse_args()
    public,candidate=build(ROOT,a.data_dir,a.output,a.identity,a.recovery_archive,a.recovery_sha)
    print(json.dumps({'public':public['archive_sha256'],'candidate':candidate['archive_sha256']}))
