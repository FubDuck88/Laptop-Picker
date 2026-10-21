"""Allowlisted deterministic Pages archives; fixtures and diagnostics cannot be inputs."""
import hashlib
import io
import json
from pathlib import Path
import re
import tarfile

from release_pipeline import load_release, timestamp


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_archive(files, folder, *, kind, release_sha=None, prefix=''):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    for name in files:
        if not re.fullmatch(r'[A-Za-z0-9_./-]+', name) or '..' in name.split('/') or name.startswith('/'):
            raise ValueError('Unsafe archive path')
        if any(x in name.split('/') for x in ('tests', 'artifacts', '__pycache__', '.git', '.github')) or 'diagnostic' in name:
            raise ValueError('Excluded deployment input')
    # Match the Pages upload action: an explicit ./ root and parent directories.
    # A flat tar list is locally extractable but is not its normal deployment layout.
    with tarfile.open(folder/'artifact.tar', 'w', format=tarfile.GNU_FORMAT) as tar:
        directories={'.'}
        for name in files:
            directories.update(str(parent) for parent in Path(name).parents if str(parent)!='.')
        for name in sorted(directories,key=lambda n:(len(n.split('/')),n)):
            entry=tarfile.TarInfo('.' if name=='.' else './'+name)
            entry.type=tarfile.DIRTYPE
            entry.mode=0o755
            entry.mtime=0
            tar.addfile(entry)
        for name, body in sorted(files.items()):
            item = tarfile.TarInfo('./'+name)
            item.size, item.mode, item.mtime = len(body), 0o644, 0
            tar.addfile(item, io.BytesIO(body))
    manifest = {'manifest_version':1, 'kind':kind, 'archive_sha256':sha((folder/'artifact.tar').read_bytes()),
                'release_sha256':release_sha, 'candidate_prefix':prefix,
                'files':{name:sha(body) for name,body in sorted(files.items())}}
    (folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    (folder/'archive.sha256').write_text(manifest['archive_sha256']+'  artifact.tar\n',encoding='ascii')
    return manifest


def read_archive(path, expected_sha):
    path = Path(path)
    if sha(path.read_bytes()) != expected_sha:
        raise ValueError('Recovery archive digest mismatch')
    files = {}
    with tarfile.open(path, 'r') as tar:
        for member in tar.getmembers():
            name=member.name.removeprefix('./')
            if member.name=='.' and member.isdir():continue
            if name.startswith('/') or '..' in name.split('/'):
                raise ValueError('Unsafe recovery archive member')
            if member.isdir():continue
            if not member.isfile() or member.size > 40*1024*1024 or name in files:
                raise ValueError('Invalid or duplicate archive member')
            files[name] = tar.extractfile(member).read()
    return files


def build(root, data_dir, output, deployment_id, recovery_archive, recovery_sha, *, as_of=None):
    root, data_dir, output = Path(root), Path(data_dir), Path(output)
    if not re.fullmatch(r'[A-Za-z0-9-]+', deployment_id):
        raise ValueError('Invalid deployment identity')
    release = load_release(data_dir)
    if not release:
        raise ValueError('No validated release')
    from datetime import datetime, timezone, timedelta
    if not any((as_of or datetime.now(timezone.utc))-timestamp(o['observed_at']) < timedelta(days=7)
               for o in release['catalog']['offers']):
        raise ValueError('No eligible offers for cutover')
    pointer = json.loads((data_dir/'current.json').read_text(encoding='utf-8'))
    names = ['index.html','mobile.html','analytics.html']
    names += ['js/'+name+'.js' for name in ('analytics','catalog','core','desktop','mobile','release')]
    names += ['css/'+name+'.css' for name in ('analytics','catalog','mobile','styles')]
    public = {name:(root/name).read_bytes() for name in names}
    public['404.html'] = (root/'site/maintenance/index.html').read_bytes()
    public['data/current.json'] = (data_dir/'current.json').read_bytes()
    public['data/'+pointer['path']] = (data_dir/pointer['path']).read_bytes()
    public_manifest = write_archive(public,output/'public',kind='public-P',release_sha=pointer['sha256'])
    candidate = read_archive(recovery_archive,recovery_sha)
    prefix = 'candidate/'+deployment_id+'/'
    for name,body in public.items():
        if name.endswith('.html'):
            body = body.replace(b'<head>',b'<head>\n<meta name="robots" content="noindex,nofollow">',1)
        candidate[prefix+name] = body
    candidate_manifest = write_archive(candidate,output/'candidate',kind='candidate-C',release_sha=pointer['sha256'],prefix=prefix)
    return public_manifest,candidate_manifest
