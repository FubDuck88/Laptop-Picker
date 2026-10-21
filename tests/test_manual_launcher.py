from unittest.mock import patch,Mock
import unittest
import scrape_and_compile


class LauncherTests(unittest.TestCase):
    def test_collection_failure_propagates_and_stops_validation(self):
        with patch('scrape_and_compile.subprocess.run',return_value=Mock(returncode=7)) as run:
            self.assertEqual(scrape_and_compile.main(),7)
            self.assertEqual(run.call_count,1)
            self.assertIn('--sources',run.call_args.args[0])

    def test_success_is_followed_by_verification_and_its_status_propagates(self):
        with patch('scrape_and_compile.subprocess.run',side_effect=[Mock(returncode=0),Mock(returncode=9)]) as run:
            self.assertEqual(scrape_and_compile.main(),9)
            self.assertEqual(run.call_count,2)
            self.assertIn('--validate',run.call_args.args[0])
