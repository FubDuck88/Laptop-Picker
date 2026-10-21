"""Offline behavior tests. Expected failures describe unfixed Phase 2/3 defects."""

from contextlib import ExitStack, redirect_stdout
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import sys

# The legacy repository contains tracked bytecode; never rewrite it on import.
sys.dont_write_bytecode = True

import run_all
from scrapers import allit_scraper, asus_scraper, pcimage_scraper
from source_normalization import is_family_level


FIXTURES = Path(__file__).parent / "fixtures"
CASES = json.loads((FIXTURES / "regressions.json").read_text(encoding="utf-8"))
SNAPSHOTS = json.loads((FIXTURES / "source_snapshots.json").read_text(encoding="utf-8"))


def compile_sources(sources):
    """Exercise the real compiler and exports, isolating every write in a temp dir."""
    with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
        data_dir = Path(directory)
        for filename, rows in sources.items():
            fields = sorted({key for row in rows for key in row})
            with (data_dir / filename).open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
        stack.enter_context(patch.object(run_all, "MASTER_DIR", directory))
        stack.enter_context(patch.object(run_all, "DATA_DIR", directory))
        stack.enter_context(patch.object(run_all, "MASTER_FILE", str(data_dir / "master_laptops.csv")))
        stack.enter_context(redirect_stdout(io.StringIO()))
        run_all.combine_all_csvs()
        return json.loads((data_dir / "laptops.json").read_text(encoding="utf-8"))


class CompilerBaselineTests(unittest.TestCase):
    def setUp(self):
        # Execute production code outside expectedFailure's scope: unexpected
        # exceptions are setup errors, not accepted reproductions of a defect.
        preparations = {
            "test_bug_01_acer_fallback_keeps_actual_allit_seller": lambda: run_all.clean_vendor_name("Acer (via ALL IT)", "acer_laptops.csv"),
            "test_bug_02_conflicting_configurations_never_share_a_price": lambda: compile_sources({
                "allit_laptops.csv": [CASES["conflicting_offers"][0]],
                "pcimage_laptops.csv": [CASES["conflicting_offers"][1]],
            }),
            "test_bug_03_family_maxima_are_not_exact_priced_configurations": lambda: compile_sources({"asus_laptops.csv": [CASES["family_offer"]]}),
            "test_bug_04_generic_title_words_are_not_part_numbers": lambda: run_all.extract_part_number("Acer Acer Aspire 7 Laptop", "4711721057414"),
        }
        prepare = preparations.get(self._testMethodName)
        if prepare:
            self.observed = prepare()

    def test_every_populated_source_has_a_frozen_compiler_input(self):
        populated = {path.name for path in (Path(run_all.MASTER_DIR) / "data").glob("*_laptops.csv")
                     if path.name != "master_laptops.csv"}
        self.assertEqual(set(SNAPSHOTS["sources"]), populated)
        self.assertTrue(SNAPSHOTS["source_commit"])
        for filename, row in SNAPSHOTS["sources"].items():
            with self.subTest(source=filename):
                self.assertTrue(row["id"])
                self.assertTrue(row["title"])
                # Compatibility check only: acceptance by the old compiler does not verify an offer.
                result = compile_sources({filename: [row]})
                expected = 0 if is_family_level(row) else 1
                self.assertEqual(len(result), expected)
                if expected:
                    self.assertEqual(result[0]["title"], row["title"])

    def test_identical_configurations_compare_prices_and_keep_seller_links(self):
        first = CASES["conflicting_offers"][0].copy()
        second = {**first, "price": "4299.00", "url": "https://seller-b.example/laptop"}
        rows = compile_sources({"allit_laptops.csv": [first], "pcimage_laptops.csv": [second]})
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["price"], "3999.00")
        self.assertEqual(rows[0]["vendor_count"], 2)
        self.assertIn("ALL IT: https://seller-a.example/laptop", rows[0]["vendor_urls"])
        self.assertIn("PC Image: https://seller-b.example/laptop", rows[0]["vendor_urls"])

    def test_untitled_and_missing_identifier_records_are_excluded(self):
        rows = compile_sources({"allit_laptops.csv": [
            {"id": "bad-title", "title": "Untitled model", "price": "1000"},
            {"id": "", "title": "Laptop", "price": "1000"},
        ]})
        self.assertEqual(rows, [])

    def test_bug_01_acer_fallback_keeps_actual_allit_seller(self):
        self.assertEqual(self.observed, "ALL IT")

    def test_bug_02_conflicting_configurations_never_share_a_price(self):
        self.assertEqual(len(self.observed), 2, "16GB/512GB and 32GB/1TB must remain separate")

    def test_bug_03_family_maxima_are_not_exact_priced_configurations(self):
        self.assertEqual(self.observed, [], "A family-level 'up to' record cannot be a verified offer")

    def test_bug_04_generic_title_words_are_not_part_numbers(self):
        self.assertIsNone(self.observed)


class ScraperBaselineTests(unittest.TestCase):
    def setUp(self):
        if self._testMethodName == "test_bug_05_gpu_memory_is_not_system_ram":
            self.observed = pcimage_scraper.parse_specs_from_title("Laptop RTX4060 8GB GDDR6 / 32GB DDR5 / 1TB SSD")
        elif self._testMethodName == "test_bug_06_shopify_variants_keep_their_own_prices_and_memory":
            # No network or sleeps: feed a source-shaped payload to the collector.
            with patch.object(allit_scraper, "create_session", return_value=Mock(headers={})), \
                 patch.object(allit_scraper.time, "sleep"), \
                 patch.object(allit_scraper, "fetch_json_with_retry", return_value={"products": [CASES["shopify_variants"]]}), \
                 redirect_stdout(io.StringIO()):
                self.observed = allit_scraper.scrape_allit()

    def test_title_parser_distinguishes_explicit_ram_and_storage(self):
        specs = pcimage_scraper.parse_specs_from_title("HP i7-13650HX/16GB DDR5/512GB SSD/RTX4060")
        self.assertEqual(specs["memory"], "16GB DDR5")
        self.assertEqual(specs["storage"], "512GB SSD")

    def test_empty_asus_specs_stay_empty_before_inference(self):
        self.assertTrue(all(value == "" for value in asus_scraper.parse_model_spec("").values()))

    def test_bug_05_gpu_memory_is_not_system_ram(self):
        self.assertEqual(self.observed["memory"], "32GB DDR5")

    def test_bug_06_shopify_variants_keep_their_own_prices_and_memory(self):
        rows = self.observed
        self.assertEqual({row["id"] for row in rows}, {"HP-16", "HP-32"})
        by_id = {row["id"]: row for row in rows}
        self.assertEqual(by_id["HP-16"]["price"], "3999.00")
        self.assertIn("16GB", by_id["HP-16"]["memory"])
        self.assertEqual(by_id["HP-32"]["price"], "4499.00")
        self.assertIn("32GB", by_id["HP-32"]["memory"])


if __name__ == "__main__":
    unittest.main()
