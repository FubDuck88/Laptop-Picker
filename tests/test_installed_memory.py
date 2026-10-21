"""Installed RAM must survive both source normalization and UI migration."""
import unittest
from source_normalization import capacity


class InstalledMemoryTests(unittest.TestCase):
    def test_two_eight_gb_modules_are_sixteen_gb_in_either_notation(self):
        for raw in ('8GB*2 DDR4-3200', '8GB x 2 DDR4', '2 x 8GB DDR4'):
            with self.subTest(raw=raw):
                self.assertEqual(capacity(raw, 'memory')['capacity_gb'], 16)


if __name__ == '__main__':
    unittest.main()
