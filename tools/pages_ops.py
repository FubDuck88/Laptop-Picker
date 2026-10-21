"""Trusted deployment state and durable archive operations for GitHub Actions."""
import argparse
import base64
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import requests

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from pages_package import read_archive, sha

BRANCH='codex/deployment-state'
OWNER='FubDuck88'
REPO='FubDuck88/Laptop-Picker'


class Github:
    def __init__(self):
        if os.environ.get('GITHUB_REPOSITORY',REPO)!=REPO:
            raise ValueError('Unexpected deployment repository')
        self.session=requests.Session()
        self.session.headers.update({'Authorization':'Bearer '+os.environ['GH_TOKEN'],
             'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'})

    def api(self,path,method='GET',data=None,allow=()):
        response=self.session.request(method,'https://api.github.com/repos/'+REPO+path,json=data,timeout=(10,30))
        if response.status_code in allow:return None
        response.raise_for_status()
        return response.json() if response.content else None

    def state(self):
        value=self.api('/contents/state.json?ref='+BRANCH,allow=(404,))
        if value is None:
            ref=self.api('/git/ref/heads/'+BRANCH,allow=(404,))
            if ref is None:
                head=self.api('/git/ref/heads/main')['object']['sha']
                self.api('/git/refs','POST',{'ref':'refs/heads/'+BRANCH,'sha':head},allow=(422,))
            state={'version':1,'maintenance':json.loads((ROOT/'deployments/maintenance.json').read_text()),
                   'public':None,'active_attempt':None,'last_schedule':None,
                   'notification':{'issue':None,'receipt_confirmed':False},'publication_inhibited':True}
            return state,None
        return json.loads(base64.b64decode(value['content'])),value['sha']

    def save(self,state,version):
        body={'message':'Record actual Pages operation','branch':BRANCH,
              'content':base64.b64encode((json.dumps(state,indent=2)+'\n').encode()).decode()}
        if version:body['sha']=version
        self.api('/contents/state.json','PUT',body)


def run_id():return os.environ['GITHUB_RUN_ID']
def now():return datetime.now(timezone.utc).isoformat()


def download(pin,destination):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    for name in ['artifact.tar','manifest.json']:
        url='https://github.com/'+REPO+'/releases/download/'+pin['tag']+'/'+name
        response=requests.get(url,timeout=(10,45));response.raise_for_status()
        if len(response.content)>45*1024*1024:raise ValueError('Archive budget exceeded')
        (destination/name).write_bytes(response.content)
    files=read_archive(destination/'artifact.tar',pin['archive_sha256'])
    manifest=json.loads((destination/'manifest.json').read_text(encoding='utf-8'))
    if {name:sha(body) for name,body in files.items()}!=manifest['files']:
        raise ValueError('Recovery file manifest mismatch')
    if manifest['archive_sha256']!=pin['archive_sha256']:raise ValueError('Wrong recovery manifest')
    return manifest


def receipt_seen(github,state):
    issue=state['notification'].get('issue')
    if not issue:return False
    comments=github.api(f'/issues/{issue}/comments?per_page=100')
    return any(c['user']['login'].casefold()==OWNER.casefold() and
               re.fullmatch(r'\s*(?:notification received|received|acknowledged)[.!]?\s*',c['body'],re.I)
               for c in comments)


def delivery_verified(state):
    """A read-only authenticated recipient-inbox check proves actual delivery."""
    proof=state['notification'].get('delivery_verified') or {}
    return (proof.get('recipient')==OWNER and proof.get('issue')==state['notification'].get('issue')
            and proof.get('method')=='authenticated_repository_notifications_api'
            and bool(re.fullmatch('[a-f0-9]{64}',proof.get('evidence_sha256',''))))


def prepare(github,mode,output,expected_run=None):
    if mode not in ('drill','cutover','daily','recover'):
        raise ValueError('Unknown publication mode')
    state,version=github.state()
    if mode=='daily' and state['publication_inhibited']:raise ValueError('Publication inhibited until approved cutover')
    if mode=='cutover':
        state['notification']['receipt_confirmed']=state['notification'].get('receipt_confirmed') or receipt_seen(github,state)
        if not state['notification']['receipt_confirmed'] and not delivery_verified(state):
            raise ValueError('Owner notification receipt is not yet confirmed')
        if not (state.get('recovery_drill') or {}).get('passed'):
            raise ValueError('Complete controlled recovery drill has not passed')
    if mode=='recover':
        if not expected_run or str((state.get('active_attempt') or {}).get('run_id'))!=str(expected_run):
            raise ValueError('Stale recovery event; refusing to overwrite newer deployment')
    pin=state.get('public') or state['maintenance']
    manifest=download(pin,Path(output)/'recovery')
    (Path(output)/'operation.json').write_text(json.dumps({'mode':mode,'recovery':pin,'manifest':manifest},indent=2)+'\n')
    if mode!='recover':
        state['active_attempt']={'run_id':run_id(),'mode':mode,'started_at':now(),'source_commit':os.environ['GITHUB_SHA']}
    github.save(state,version)
    print('Recovered archive bytes verified; operation prepared.',flush=True)


def publish_public(github,output):
    folder=Path(output)/'public';m=json.loads((folder/'manifest.json').read_text())
    tag='pages-'+run_id()+'-'+os.environ.get('GITHUB_RUN_ATTEMPT','1')
    subprocess.run(['gh','release','create',tag,str(folder/'artifact.tar'),str(folder/'manifest.json'),
        str(folder/'archive.sha256'),'--target',os.environ['GITHUB_SHA'],'--title','Verified Pages candidate archive',
        '--notes','Checked runtime-only artifact; release SHA-256 '+m['release_sha256'],'--latest=false'],check=True)
    release=github.api('/releases/tags/'+tag)
    from release_pipeline import load_release
    release_data=load_release(ROOT/'data')
    pin={'kind':'public-P','tag':tag,'release_id':release['id'],'archive_sha256':m['archive_sha256'],
         'release_sha256':m['release_sha256'],'source_commit':os.environ['GITHUB_SHA'],
         'observed_at':max(o['observed_at'] for o in release_data['catalog']['offers'])}
    (Path(output)/'public-pin.json').write_text(json.dumps(pin,indent=2)+'\n')


def finish(github,output,outcome):
    state,version=github.state();active=state.get('active_attempt') or {}
    mode=os.environ.get('OP_MODE','')
    expected=os.environ.get('RECOVER_RUN') if mode=='recover' else run_id()
    if str(active.get('run_id'))!=str(expected):raise ValueError('Stale operation cannot update deployment state')
    if outcome=='verified':
        state['public']=json.loads((Path(output)/'public-pin.json').read_text())
        state.setdefault('cutover_at',now())
        state['publication_inhibited']=False
        if os.environ.get('GITHUB_EVENT_NAME')=='schedule':
            state['last_schedule']={'run_id':run_id(),'recorded_at':now(),'event':'schedule','passed':True,
                                    'release_sha256':state['public']['release_sha256']}
    else:
        state['publication_inhibited']=state.get('public') is None or outcome not in ('drill-restored','degraded-retained')
        if outcome=='drill-restored' and state.get('public'):state['publication_inhibited']=False
        if outcome=='drill-restored':
            state['recovery_drill']={'passed':True,'run_id':run_id(),'recorded_at':now(),
                                     'detected':['http','hash','frontend']}
    state['last_operation']={'run_id':run_id(),'mode':mode,'outcome':outcome,'recorded_at':now()}
    if outcome!='recovery-unproven':state['active_attempt']=None
    github.save(state,version)


def notify(github,outcome):
    state,version=github.state()
    issue=state['notification'].get('issue')
    pin=state.get('public') or state['maintenance']
    body=(f'@{OWNER} — Phase 6R operational notification: **{outcome}**.\n\n'
          f'Run: https://github.com/{REPO}/actions/runs/{run_id()}\n\n'
          f'Retained/restored release: `{pin.get("release_sha256","maintenance")}`. '
          f'Last real observation: `{pin.get("observed_at","no live catalog in maintenance")}`.\n\n'
          'The controlled drill keeps maintenance visible and restores the stored archive. '
          'A real failed publication retains/restores the recorded known-good release. '
          'Check the run for recovery outcome; no successful recovery is implied by issue creation.\n\n'
          'If delivery cannot be verified through the authenticated recipient inbox, comment exactly **received** '
          'after this notification reaches you. Delivery proof does not approve source data or design.')
    if issue:
        github.api(f'/issues/{issue}/comments','POST',{'body':body})
    else:
        issue=github.api('/issues','POST',{'title':'Laptop Picker operational incident / 6R notification test',
                     'body':body,'assignees':[OWNER]})['number']
        state['notification']['issue']=issue;github.save(state,version)
    print(f'https://github.com/{REPO}/issues/{issue}')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['prepare','publish','finish','notify','watchdog'])
    p.add_argument('--output',type=Path,default=ROOT/'artifacts/pages')
    p.add_argument('--outcome',default='failed/degraded')
    p.add_argument('--mode',default=os.environ.get('OP_MODE','drill'))
    p.add_argument('--expected-run',default=os.environ.get('RECOVER_RUN'))
    a=p.parse_args();g=Github()
    if a.command=='prepare':prepare(g,a.mode,a.output,a.expected_run)
    elif a.command=='publish':publish_public(g,a.output)
    elif a.command=='finish':finish(g,a.output,a.outcome)
    elif a.command=='notify':notify(g,a.outcome)
    else:
        state,_=g.state();last=state.get('last_schedule') or {}
        if not state.get('public'):
            print('Maintenance remains intentional; no public schedule expected yet.');sys.exit(0)
        from datetime import timedelta
        today=datetime.now(timezone(timedelta(hours=8))).date().isoformat()
        recorded=last.get('recorded_at','')
        local_day=datetime.fromisoformat(recorded).astimezone(timezone(timedelta(hours=8))).date().isoformat() if recorded else ''
        if local_day!=today or not last.get('passed'):notify(g,'scheduled publication missing or degraded')
