"""Build a deterministic, allowlisted Pages maintenance archive (stdlib only)."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[1]
NAMES = ('index.html', 'mobile.html', 'analytics.html', '404.html')


def build(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    content = (ROOT / 'site/maintenance/index.html').read_bytes()
    if b'6r-maintenance-v1' not in content or b'noindex,nofollow' not in content:
        raise ValueError('Missing maintenance identity or indexing directive')
    archive = output / 'artifact.tar'
    with tarfile.open(archive, 'w', format=tarfile.USTAR_FORMAT) as tar:
        for name in NAMES:
            entry = tarfile.TarInfo(name)
            entry.size = len(content)
            entry.mode = 0o644
            entry.mtime = 0
            tar.addfile(entry, io.BytesIO(content))
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    manifest = {'manifest_version': 1, 'kind': 'maintenance-M',
                'archive': 'artifact.tar', 'archive_sha256': digest,
                'files': {name: hashlib.sha256(content).hexdigest() for name in NAMES}}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    (output / 'archive.sha256').write_text(digest + '  artifact.tar\n', encoding='ascii')
    # Validate archive entries and actual bytes independently of file creation.
    with tarfile.open(archive, 'r') as tar:
        if set(tar.getnames()) != set(NAMES):
            raise ValueError('Maintenance package contains unexpected paths')
        for entry in tar.getmembers():
            if not entry.isfile() or hashlib.sha256(tar.extractfile(entry).read()).hexdigest() != manifest['files'][entry.name]:
                raise ValueError('Invalid maintenance archive member')
    print(json.dumps({'archive_sha256': digest, 'files': list(NAMES)}))
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/phase6r/maintenance')
    build(parser.parse_args().output)
