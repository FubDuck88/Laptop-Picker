from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import tarfile
import unittest

from pages_package import build,read_archive,write_archive

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'tests/fixtures/releases/phase6-2026-10-20'


class PagesPackageTests(unittest.TestCase):
    def test_candidate_has_separate_pointer_and_root_stays_known_good(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp=Path(tmp)
            known={'index.html':b'maintenance','mobile.html':b'maintenance'}
            recovery=write_archive(known,tmp/'recovery',kind='maintenance-M')
            public,candidate=build(ROOT,FIXTURE,tmp/'build','test-1',tmp/'recovery/artifact.tar',
                                  recovery['archive_sha256'],as_of=datetime(2026,10,21,tzinfo=timezone.utc))
            a=read_archive(tmp/'build/candidate/artifact.tar',candidate['archive_sha256'])
            with tarfile.open(tmp/'build/candidate/artifact.tar') as archive:
                self.assertTrue(any(m.isdir() for m in archive.getmembers()))
                self.assertTrue(all('\\' not in m.name for m in archive.getmembers()))
            p=read_archive(tmp/'build/public/artifact.tar',public['archive_sha256'])
            self.assertEqual(a['index.html'],b'maintenance')
            self.assertNotIn('data/current.json',a)
            self.assertIn('candidate/test-1/data/current.json',a)
            self.assertEqual(a['candidate/test-1/data/current.json'],p['data/current.json'])
            self.assertIn(b'noindex,nofollow',a['candidate/test-1/index.html'])
            self.assertFalse(any('candidate/' in x or 'tests/' in x or 'diagnostic' in x for x in p))
            original=json.loads((FIXTURE/'manifest.json').read_text())['source_release_sha256']
            self.assertEqual(public['release_sha256'],original)

    def test_changed_recovery_bytes_and_excluded_paths_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp=Path(tmp)
            m=write_archive({'index.html':b'maintenance'},tmp,kind='maintenance-M')
            (tmp/'artifact.tar').write_bytes(b'tampered')
            with self.assertRaisesRegex(ValueError,'digest mismatch'):read_archive(tmp/'artifact.tar',m['archive_sha256'])
            for name in ['tests/fixture.json','data/catalog.diagnostics.json','../escape','/absolute']:
                with self.assertRaises(ValueError):write_archive({name:b'bad'},tmp,kind='candidate-C')

    def test_expired_data_cannot_be_a_new_cutover(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp=Path(tmp);m=write_archive({'index.html':b'M'},tmp/'recovery',kind='maintenance-M')
            with self.assertRaisesRegex(ValueError,'eligible offers'):
                build(ROOT,FIXTURE,tmp/'build','expired',tmp/'recovery/artifact.tar',m['archive_sha256'],
                      as_of=datetime(2026,11,1,tzinfo=timezone.utc))
