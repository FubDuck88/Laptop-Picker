"""Exercise the same catalog interface future source adapters will use."""

from copy import deepcopy
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True

from catalog_v2 import (CatalogValidationError, SourceResult, build_catalog,
                        build_legacy_catalog, validate_catalog, write_catalog)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / "tests/fixtures/catalog_v2_record.json").read_text(encoding="utf-8"))
GENERATED = "2026-10-20T00:31:00Z"


def record():
    return deepcopy(FIXTURE["record"])


def source(records=None, **changes):
    values = {"source_id": "test_store", "status": "complete", "records": [record()] if records is None else records,
              "started_at": "2026-10-20T00:00:00Z", "finished_at": "2026-10-20T00:30:00Z"}
    return SourceResult(**{**values, **changes})


def build(records=None, **changes):
    return build_catalog([source(records, **changes)], generated_at=GENERATED)


class CatalogContractTests(unittest.TestCase):
    def assertRejected(self, candidate, code=None):
        result = build([candidate])
        self.assertEqual(result.catalog["offers"], [])
        self.assertEqual(result.catalog["configurations"], [])
        self.assertEqual(result.catalog["observations"], [])
        report = result.catalog["run_reports"][0]
        self.assertEqual(report["rejected_count"], 1)
        self.assertEqual(report["accepted_count"], 0)
        if code:
            self.assertIn(code, {issue["code"] for issue in report["issues"]})
        return result

    def test_complete_exact_offer_has_separate_configuration_price_and_observation(self):
        candidate = record()
        unchanged = deepcopy(candidate)
        result = build([candidate])
        self.assertEqual(candidate, unchanged)
        configuration, = result.catalog["configurations"]
        offer, = result.catalog["offers"]
        observation, = result.catalog["observations"]
        self.assertEqual(result.catalog["schema_version"], 2)
        self.assertEqual(configuration["memory"], {"capacity_gb": 16, "label": "16GB DDR5"})
        self.assertEqual(configuration["storage"], {"capacity_gb": 1000, "label": "1TB SSD"})
        self.assertEqual(offer["price_sen"], 399900)
        self.assertEqual(offer["configuration_id"], configuration["id"])
        self.assertEqual(observation["offer_id"], offer["id"])
        self.assertEqual(observation["observed_at"], candidate["offer"]["observed_at"])
        self.assertEqual(result.catalog["run_reports"][0]["accepted_count"], 1)
        self.assertEqual(result.diagnostics["records"], [])
        validate_catalog(json.loads(json.dumps(result.catalog)))

    def test_unknown_hardware_and_availability_remain_explicit_without_inference(self):
        candidate = record()
        for name in ("cpu_model", "gpu_model", "gpu_kind", "vram_gb", "memory", "storage", "display"):
            candidate["configuration"].pop(name)
            candidate["configuration"]["evidence"].pop(name)
        candidate["offer"].pop("availability")
        candidate["offer"]["evidence"].pop("availability")
        result = build([candidate]).catalog
        configuration, = result["configurations"]
        self.assertIsNone(configuration["cpu_model"])
        self.assertIsNone(configuration["gpu_model"])
        self.assertIsNone(configuration["memory"]["capacity_gb"])
        self.assertIsNone(configuration["battery_wh"])
        self.assertEqual(configuration["gpu_kind"], "unknown")
        self.assertEqual(result["offers"][0]["availability"], "unknown")

    def test_decimal_prices_are_exact_and_invalid_money_is_never_rounded_or_salvaged(self):
        for amount, expected in (("0.01", 1), ("3999.90", 399990), ("RM 3,999.00", 399900)):
            with self.subTest(amount=amount):
                candidate = record()
                candidate["offer"]["price_myr"] = amount
                candidate["offer"]["evidence"]["price"]["raw_value"] = amount
                self.assertEqual(build([candidate]).catalog["offers"][0]["price_sen"], expected)
        for amount in ("0", "-1", "NaN", "Infinity", "1e3", "3999.999", "3,99", "3999-4499", "RM 100/month", "", 3999.99, True):
            with self.subTest(amount=amount):
                candidate = record()
                candidate["offer"]["price_myr"] = amount
                self.assertRejected(candidate, "invalid_record")

    def test_wrong_currency_conditional_price_and_conflicting_price_evidence_are_rejected(self):
        for name, value in (("currency", "USD"), ("price_myr", "RM 3999 with voucher"), ("price_basis", "membership")):
            with self.subTest(field=name):
                candidate = record()
                candidate["offer"][name] = value
                self.assertRejected(candidate)
        candidate = record()
        candidate["offer"]["evidence"]["price"]["raw_value"] = "4499.00"
        self.assertRejected(candidate, "conflicting_price")

    def test_preconverted_sen_requires_an_integer_and_one_explicit_unit(self):
        candidate = record()
        candidate["offer"].pop("price_myr")
        candidate["offer"]["price_sen"] = 399900
        self.assertEqual(build([candidate]).catalog["offers"][0]["price_sen"], 399900)
        for value in (399900.0, True, "399900", 0, -100):
            with self.subTest(value=value):
                invalid = deepcopy(candidate)
                invalid["offer"]["price_sen"] = value
                self.assertRejected(invalid)
        candidate["offer"]["price_myr"] = "3999.00"
        self.assertRejected(candidate, "invalid_record")

    def test_family_maxima_ambiguous_identity_and_non_laptops_are_rejected(self):
        for name, value in (("identity_scope", "family"), ("manufacturer_part_number", "ACER ACER ASPIRE"),
                            ("manufacturer_part_number", "SKU-A/SKU-B"), ("product_type", "desktop"),
                            ("cpu_model", "Up to Intel Core Ultra 7"), ("title", "Starting from HP Laptop"),
                            ("cpu_model", "Intel Core i5 or Core i7"), ("gpu_model", "RTX 4060 / RTX 4070")):
            with self.subTest(field=name):
                candidate = record()
                candidate["configuration"][name] = value
                self.assertRejected(candidate)
        candidate = record()
        candidate["configuration"]["memory"]["label"] = "Up to 32GB DDR5"
        self.assertRejected(candidate, "family_level")

    def test_normalized_capacities_must_agree_with_labels_and_not_vram(self):
        for capacity in ({"capacity_gb": 32, "label": "16GB DDR5"}, {"capacity_gb": 8, "label": "8GB GDDR6"},
                         {"capacity_gb": 16, "label": "16GB / 32GB"}, {"capacity_gb": True, "label": "16GB"},
                         {"capacity_gb": 16, "label": None}, {"capacity_gb": None, "label": "16GB / 32GB"}):
            with self.subTest(capacity=capacity):
                candidate = record()
                candidate["configuration"]["memory"] = capacity
                self.assertRejected(candidate)
        candidate = record()
        candidate["configuration"]["memory"] = {"capacity_gb": 32, "label": "2x16GB DDR5"}
        self.assertEqual(len(build([candidate]).catalog["offers"]), 1)

    def test_missing_or_untrusted_evidence_is_rejected(self):
        for group, name in (("configuration", "manufacturer_part_number"), ("configuration", "memory"),
                            ("offer", "seller"), ("offer", "variant_id"), ("offer", "price"), ("offer", "availability")):
            with self.subTest(group=group, field=name):
                candidate = record()
                candidate[group]["evidence"].pop(name)
                self.assertRejected(candidate, "missing_evidence")
        candidate = record()
        candidate["offer"]["evidence"]["price"]["method"] = "legacy_csv"
        self.assertRejected(candidate, "schema")

    def test_specification_conflicts_and_unrelated_marketing_fields_are_rejected(self):
        for group, name, value in (("configuration", "others", "Fastest laptop ever"),
                                   ("configuration", "battery_wh", -5), ("configuration", "vram_gb", 0),
                                   ("offer", "condition", "refurbished"), ("offer", "availability", "probably")):
            with self.subTest(field=name):
                candidate = record()
                candidate[group][name] = value
                self.assertRejected(candidate, "schema")
        candidate = record()
        candidate["configuration"]["display"]["resolution_height"] = None
        self.assertRejected(candidate, "incomplete_resolution")
        candidate = record()
        candidate["configuration"]["gpu_kind"] = "integrated"
        self.assertRejected(candidate, "integrated_vram")

    def test_display_values_must_not_contradict_explicit_labels(self):
        for changes in ({"diagonal_inches": 16}, {"refresh_hz": 60}, {"label": "15.6 inch 1920x1080 / 2560x1440"},
                        {"label": "16 inch 2560x1440 165Hz"}, {"label": None}):
            with self.subTest(changes=changes):
                candidate = record()
                candidate["configuration"]["display"].update(changes)
                self.assertRejected(candidate)

    def test_invalid_purchase_and_evidence_urls_are_rejected(self):
        for url in ("javascript:alert(1)", "file:///product", "https://user:secret@shop.example/item", "https:///missing-host", "https://shop.example:bad/item", "https://shop.example/a b"):
            for target in ("offer", "evidence"):
                with self.subTest(url=url, target=target):
                    candidate = record()
                    if target == "offer":
                        candidate["offer"]["url"] = url
                    else:
                        candidate["offer"]["evidence"]["price"]["source_url"] = url
                    self.assertRejected(candidate)

    def test_observation_times_are_explicit_valid_and_not_fabricated_from_build_time(self):
        for value in (None, "", "2026-10-20", "2026-10-20T00:15:00", "2026-02-30T00:15:00Z", "2026-10-21T00:15:00Z",
                      "2026-10-20T00:15:00+08:99", "2026-10-20T00:15:00.1234567Z"):
            with self.subTest(time=value):
                candidate = record()
                candidate["offer"]["observed_at"] = value
                self.assertRejected(candidate)
        candidate = record()
        candidate["offer"]["evidence"]["price"]["observed_at"] = "2026-10-20T00:14:00Z"
        self.assertRejected(candidate, "stale_evidence")
        candidate = record()
        candidate["configuration"]["evidence"]["memory"]["observed_at"] = "2026-10-20T00:16:00Z"
        self.assertRejected(candidate, "future_evidence")
        self.assertEqual(build().catalog["observations"][0]["observed_at"], "2026-10-20T00:15:00Z")

    def test_ids_are_stable_for_price_changes_and_isolated_for_configuration_changes(self):
        original = build().catalog
        candidate = record()
        candidate["offer"]["price_myr"] = "3899.00"
        candidate["offer"]["evidence"]["price"]["raw_value"] = "3899.00"
        cheaper = build([candidate]).catalog
        self.assertEqual(original["offers"][0]["id"], cheaper["offers"][0]["id"])
        self.assertEqual(original["configurations"][0]["id"], cheaper["configurations"][0]["id"])
        candidate["configuration"]["memory"] = {"capacity_gb": 32, "label": "32GB DDR5"}
        upgraded = build([candidate]).catalog
        self.assertNotEqual(original["offers"][0]["id"], upgraded["offers"][0]["id"])
        self.assertNotEqual(original["configurations"][0]["id"], upgraded["configurations"][0]["id"])

    def test_equivalent_timezone_instants_have_the_same_observation_id(self):
        original = build().catalog
        candidate = record()
        candidate["offer"]["observed_at"] = "2026-10-20T08:15:00+08:00"
        self.assertEqual(original["observations"][0]["id"], build([candidate]).catalog["observations"][0]["id"])

    def test_duplicate_and_conflicting_variants_do_not_silently_win_by_order(self):
        duplicated = build([record(), record()]).catalog
        self.assertEqual(len(duplicated["offers"]), 1)
        self.assertEqual(duplicated["run_reports"][0]["rejected_count"], 1)
        upgraded = record()
        upgraded["configuration"]["memory"] = {"capacity_gb": 32, "label": "32GB DDR5"}
        for records in ([record(), upgraded], [upgraded, record()]):
            result = build(records).catalog
            self.assertEqual(result["offers"], [])
            self.assertEqual(result["run_reports"][0]["rejected_count"], 2)
            self.assertEqual({issue["code"] for issue in result["run_reports"][0]["issues"]}, {"conflicting_variant"})
        repriced = record()
        repriced["offer"]["price_myr"] = "4499.00"
        repriced["offer"]["evidence"]["price"]["raw_value"] = "4499.00"
        self.assertEqual(build([record(), repriced]).catalog["offers"], [])

    def test_separate_sellers_are_not_automatically_cross_store_matches(self):
        result = build_catalog([source(source_id="seller_b"), source(source_id="seller_a")], generated_at=GENERATED).catalog
        self.assertEqual(len(result["configurations"]), 2)
        self.assertEqual(len(result["offers"]), 2)
        self.assertEqual([report["source_id"] for report in result["run_reports"]], ["seller_a", "seller_b"])

    def test_partial_and_failed_sources_have_reports_but_no_new_offers(self):
        for status in ("partial", "failed"):
            result = build(status=status, error="Pagination failed").catalog
            self.assertEqual(result["offers"], [])
            self.assertEqual(result["observations"], [])
            self.assertEqual(result["run_reports"][0]["status"], status)
            self.assertEqual(result["run_reports"][0]["rejected_count"], 1)

    def test_malformed_run_metadata_fails_instead_of_publishing(self):
        for changes in ({"started_at": None}, {"finished_at": "2026-10-19T23:59:00Z"},
                        {"status": "failed", "error": None}, {"status": "not_run"}, {"source_id": "bad source"},
                        {"mode": "invalid"}, {"records": "not a list"}):
            with self.subTest(changes=changes):
                with self.assertRaises(CatalogValidationError):
                    build(**changes)
        with self.assertRaises(CatalogValidationError):
            build_catalog([source(), source()], generated_at=GENERATED)

    def test_validation_rejects_broken_references_duplicate_ids_and_counts(self):
        for mutation in ("version", "reference", "duplicate", "counts", "observation", "missing_observation", "unknown_property"):
            with self.subTest(mutation=mutation):
                catalog = deepcopy(build().catalog)
                if mutation == "version": catalog["schema_version"] = 3
                if mutation == "reference": catalog["offers"][0]["configuration_id"] = "cfg_missing"
                if mutation == "duplicate": catalog["offers"].append(deepcopy(catalog["offers"][0]))
                if mutation == "counts": catalog["run_reports"][0]["record_count"] = 2
                if mutation == "observation": catalog["observations"][0]["price_sen"] = 1
                if mutation == "missing_observation": catalog["observations"] = []
                if mutation == "unknown_property": catalog["offers"][0]["marketing"] = "Best deal"
                with self.assertRaises(CatalogValidationError):
                    validate_catalog(catalog)

    def test_bad_native_input_is_diagnostic_and_does_not_block_good_records(self):
        bad = record()
        bad["configuration"]["battery_wh"] = float("nan")
        result = build([bad, record()])
        self.assertEqual(len(result.catalog["offers"]), 1)
        self.assertEqual(result.catalog["run_reports"][0]["rejected_count"], 1)
        with tempfile.TemporaryDirectory() as directory:
            write_catalog(result, directory)
            diagnostics = json.loads((Path(directory) / "catalog.v2.diagnostics.json").read_text(encoding="utf-8"))
            self.assertIn("unserializable_record", diagnostics["records"][0]["record"])


class LegacyMigrationTests(unittest.TestCase):
    def test_every_saved_source_remains_unverified_and_retains_raw_diagnostics(self):
        snapshots = json.loads((ROOT / "tests/fixtures/source_snapshots.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            paths = []
            for filename, row in snapshots["sources"].items():
                path = Path(directory) / filename
                with path.open("w", encoding="utf-8", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=list(row))
                    writer.writeheader()
                    writer.writerow(row)
                paths.append(path)
            result = build_legacy_catalog(paths, generated_at=GENERATED)
        self.assertEqual(result.catalog["configurations"], [])
        self.assertEqual(result.catalog["offers"], [])
        self.assertEqual(result.catalog["observations"], [])
        self.assertEqual(len(result.diagnostics["records"]), 10)
        for report in result.catalog["run_reports"]:
            self.assertEqual(report["status"], "not_run")
            self.assertIsNone(report["started_at"])
            self.assertIsNone(report["finished_at"])
            self.assertEqual(report["rejected_count"], 1)
            self.assertEqual(report["accepted_count"], 0)
        for item in result.diagnostics["records"]:
            self.assertEqual(item["record"], snapshots["sources"][item["input_name"]])
        self.assertTrue(any(issue["code"] == "family_level" for item in result.diagnostics["records"] for issue in item["issues"]))

    def test_failed_csv_read_is_reported_without_inventing_a_collection_time(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing_laptops.csv"
            result = build_legacy_catalog([path], generated_at=GENERATED).catalog
        report, = result["run_reports"]
        self.assertEqual(report["status"], "failed")
        self.assertTrue(report["error"])
        self.assertIsNone(report["finished_at"])

    def test_empty_source_and_master_output_do_not_create_fake_records(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty_laptops.csv"
            path.write_text("id,title,price\n", encoding="utf-8")
            master = Path(directory) / "master_laptops.csv"
            master.write_text("not an input", encoding="utf-8")
            result = build_legacy_catalog([path, master], generated_at=GENERATED).catalog
        self.assertEqual(len(result["run_reports"]), 1)
        self.assertEqual(result["run_reports"][0]["record_count"], 0)
        self.assertEqual(result["offers"], [])

    def test_writer_and_validation_command_leave_existing_catalog_intact_on_error(self):
        result = build()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "catalog.v2.json"
            write_catalog(result, directory)
            before = output.read_bytes()
            result.catalog["offers"][0]["price_sen"] = -1
            with self.assertRaises(CatalogValidationError):
                write_catalog(result, directory)
            self.assertEqual(output.read_bytes(), before)
            command = [sys.executable, "-B", "tools/build_catalog_v2.py", "--validate", str(output)]
            checked = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertEqual(output.read_bytes(), before)
            self.assertEqual(list(Path(directory).glob("*.tmp")), [])

    def test_existing_compiler_writes_sidecar_but_does_not_certify_legacy_rows(self):
        import run_all
        row = {"id": "hp-test", "title": "HP Test Laptop", "price": "3999.00", "url": "https://shop.example/laptop"}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            with (path / "allit_laptops.csv").open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(row))
                writer.writeheader()
                writer.writerow(row)
            with patch.object(run_all, "MASTER_DIR", directory), patch.object(run_all, "DATA_DIR", directory), \
                 patch.object(run_all, "MASTER_FILE", str(path / "master_laptops.csv")):
                run_all.combine_all_csvs()
            legacy = json.loads((path / "laptops.json").read_text(encoding="utf-8"))
            new = json.loads((path / "catalog.v2.json").read_text(encoding="utf-8"))
            self.assertEqual(legacy[0]["price"], "3999.00")
            self.assertEqual(new["offers"], [])
            self.assertEqual(new["run_reports"][0]["rejected_count"], 1)
            validate_catalog(new)


if __name__ == "__main__":
    unittest.main()
