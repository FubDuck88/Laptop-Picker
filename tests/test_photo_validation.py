"""HTTP failures, image payloads, and exact-configuration fallback behavior."""

from copy import deepcopy
import unittest

import requests

from photo_validation import PhotoChecker, validate_source_photos
from release_pipeline import build_release
from test_release_pipeline import result


PNG = b'\x89PNG\r\n\x1a\n' + b'payload'


class Response:
    def __init__(self, status=200, content_type='image/png', body=PNG, location=None):
        self.status_code = status
        self.headers = {'Content-Type': content_type}
        if location:
            self.headers['Location'] = location
        self.body = body
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.closed = True

    def iter_content(self, chunk_size):
        assert chunk_size == 512
        yield self.body[:chunk_size]


class Session:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def photo_result(day=20, url='https://cdn.example/old.png'):
    value = result(day)
    offer = value.records[0]['offer']
    if url:
        offer['image_url'] = url
        offer['evidence']['image_url'] = dict(offer['evidence']['url'], raw_value=url)
    return value


class PhotoValidationTests(unittest.TestCase):
    def test_bounded_read_cache_and_no_auth_retry(self):
        response = Response()
        session = Session(response, Response(403))
        checker = PhotoChecker(session, sleep=lambda _: None)
        self.assertEqual(checker.check('https://cdn.example/a.png')['state'], 'available')
        self.assertEqual(checker.check('https://cdn.example/a.png')['state'], 'available')
        self.assertTrue(response.closed)
        self.assertEqual(checker.check('https://cdn.example/private.png')['state'], 'access_denied')
        self.assertEqual(len(session.calls), 2)
        self.assertEqual(session.calls[0][1]['timeout'], (5, 10))
        self.assertFalse(session.calls[0][1]['allow_redirects'])

    def test_content_type_alone_is_not_enough_and_statuses_are_distinct(self):
        checker = PhotoChecker(Session(Response(body=b'<html>challenge</html>'), Response(404), Response(200, 'text/html')))
        self.assertEqual(checker.check('https://cdn.example/fake.png')['state'], 'not_image')
        self.assertEqual(checker.check('https://cdn.example/gone.png')['state'], 'http_error')
        self.assertEqual(checker.check('https://cdn.example/page')['state'], 'not_image')
        self.assertEqual(checker.check(None)['state'], 'missing')

    def test_transient_retries_and_redirects_are_bounded(self):
        session = Session(Response(503), requests.Timeout(), Response())
        self.assertEqual(PhotoChecker(session, sleep=lambda _: None).check('https://cdn.example/a')['state'], 'available')
        self.assertEqual(len(session.calls), 3)
        session = Session(*[Response(302, location='/again') for _ in range(4)])
        self.assertEqual(PhotoChecker(session).check('https://cdn.example/a')['state'], 'redirect_error')
        self.assertEqual(len(session.calls), 4)
        session = Session(Response(302, location='http://127.0.0.1/private'))
        self.assertEqual(PhotoChecker(session).check('https://cdn.example/a')['state'], 'url_rejected')
        self.assertEqual(len(session.calls), 1)

    def test_failed_photo_is_optional_and_price_observation_survives(self):
        value = photo_result()
        original = deepcopy(value)
        cleaned, audit = validate_source_photos([value], checker=PhotoChecker(Session(Response(404))))
        release, _ = build_release(cleaned, generated_at='2026-10-20T00:31:00Z')
        self.assertEqual(len(release['catalog']['offers']), 1)
        self.assertNotIn('image_url', release['catalog']['offers'][0])
        self.assertEqual(value, original)
        self.assertEqual(audit[0]['state'], 'unavailable')

    def test_unproven_photo_cannot_discard_a_valid_price_or_trigger_a_request(self):
        value = photo_result()
        value.records[0]['offer']['evidence'].pop('image_url')
        session = Session()
        cleaned, audit = validate_source_photos([value], checker=PhotoChecker(session))
        release, _ = build_release(cleaned, generated_at='2026-10-20T00:31:00Z')
        self.assertEqual(len(release['catalog']['offers']), 1)
        self.assertNotIn('image_url', release['catalog']['offers'][0])
        self.assertEqual(audit[0]['checks'][0]['state'], 'unproven')
        self.assertEqual(session.calls, [])

    def test_previous_photo_needs_same_hardware_and_a_fresh_successful_check(self):
        previous, _ = build_release([photo_result()], generated_at='2026-10-20T00:31:00Z')
        incoming = photo_result(21, 'https://cdn.example/gone.png')
        cleaned, audit = validate_source_photos([incoming], previous, checker=PhotoChecker(Session(Response(404), Response())), generated_at='2026-10-21T00:31:00Z')
        saved, _ = build_release(cleaned, previous, generated_at='2026-10-21T00:31:00Z')
        offer = saved['catalog']['offers'][0]
        self.assertEqual(offer['image_url'], 'https://cdn.example/old.png')
        self.assertEqual(offer['evidence']['image_url']['observed_at'], previous['catalog']['offers'][0]['evidence']['image_url']['observed_at'])
        self.assertTrue(audit[0]['retained_previous_photo'])
        self.assertEqual(len(saved['history']['receipts']), 2)
        incoming.records[0]['configuration']['memory'] = {'capacity_gb': 32, 'label': '32GB DDR5'}
        incoming.records[0]['configuration']['evidence']['memory']['raw_value'] = '32GB DDR5'
        session = Session(Response(404))
        cleaned, audit = validate_source_photos([incoming], previous, checker=PhotoChecker(session), generated_at='2026-10-21T00:31:00Z')
        self.assertNotIn('image_url', cleaned[0].records[0]['offer'])
        self.assertEqual(len(session.calls), 1)
        self.assertFalse(audit[0]['retained_previous_photo'])


if __name__ == '__main__':
    unittest.main()
